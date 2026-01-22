"""Run command for executing workflow simulations."""

import asyncio
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console

from windtunnel.actions.assert_ import AssertActionRunner
from windtunnel.actions.http import HttpActionRunner
from windtunnel.actions.wait import WaitActionRunner
from windtunnel.config.loader import load_scenarios, load_sut
from windtunnel.config.scenario import (
    Action,
    AssertAction,
    Assertion,
    HttpAction,
    Scenario,
    WaitAction,
)
from windtunnel.config.sut import SUTConfig
from windtunnel.engine.context import WorkflowContext
from windtunnel.engine.executor import (
    DEFAULT_PARALLELISM,
    InstanceResult,
    ParallelExecutor,
)
from windtunnel.engine.template import TemplateEngine
from windtunnel.models.assertion_result import AssertionResult
from windtunnel.models.manifest import RunConfig
from windtunnel.models.observation import Observation
from windtunnel.storage.artifact import ArtifactStore
from windtunnel.turbulence.engine import TurbulenceEngine

console = Console()


def run(
    sut: Path = typer.Option(
        ...,
        "--sut",
        "-s",
        help="Path to the SUT (System Under Test) configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    scenarios: Path = typer.Option(
        ...,
        "--scenarios",
        "-c",
        help="Path to the scenarios directory containing YAML workflow definitions",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    n: int = typer.Option(
        100,
        "--n",
        "-n",
        help="Number of workflow instances to run",
        min=1,
    ),
    parallel: int = typer.Option(
        DEFAULT_PARALLELISM,
        "--parallel",
        "-p",
        help="Maximum number of concurrent workflow instances",
        min=1,
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducible runs (auto-generated if not provided)",
    ),
    output_dir: Path = typer.Option(
        Path("runs"),
        "--output",
        "-o",
        help="Directory to store run artifacts",
        resolve_path=True,
    ),
) -> None:
    """Execute workflow simulations against the system under test.

    Runs N instances of the defined scenarios, executing actions and recording
    observations for later analysis. Results are stored in the output directory
    with a unique run ID.

    Example:
        windtunnel run --sut sut.yaml --scenarios scenarios/ --n 1000 --parallel 50
    """
    exit_code = asyncio.run(
        _run_instances(
            sut=sut,
            scenarios_dir=scenarios,
            instances=n,
            parallelism=parallel,
            seed=seed,
            output_dir=output_dir,
        )
    )
    raise typer.Exit(code=exit_code)


async def _run_instances(
    *,
    sut: Path,
    scenarios_dir: Path,
    instances: int,
    parallelism: int,
    seed: int | None,
    output_dir: Path,
) -> int:
    sut_config = load_sut(sut)
    scenario_list = load_scenarios(scenarios_dir)
    seed_value = seed if seed is not None else random.SystemRandom().randint(1, 2**31)

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    run_config = RunConfig(seed=seed_value, concurrency=parallelism)

    console.print("[bold blue]Windtunnel Run[/bold blue]")
    console.print(f"  Run ID: {run_id}")
    console.print(f"  SUT config: {sut}")
    console.print(f"  Scenarios: {scenarios_dir}")
    console.print(f"  Instances: {instances}")
    console.print(f"  Parallelism: {parallelism}")
    console.print(f"  Seed: {seed_value}")
    console.print(f"  Output: {output_dir}")
    console.print()

    artifact_store = ArtifactStore(
        run_id=run_id,
        base_path=output_dir,
        sut_name=sut_config.name,
        scenario_ids=[scenario.id for scenario in scenario_list],
        seed=seed_value,
        config=run_config,
    ).initialize()

    template_engine = TemplateEngine()
    executor = ParallelExecutor(parallelism=parallelism, console=console)

    async def execute_instance(instance_index: int) -> InstanceResult:
        scenario = _pick_scenario(scenario_list, seed_value, instance_index)
        entry_data = scenario.entry.model_dump()
        ctx = WorkflowContext.from_scenario_entry(entry_data, run_id=run_id)
        context_dict = ctx.to_dict()

        if scenario.source_path is not None:
            context_dict["_scenario_path"] = scenario.source_path

        instance_sut = sut_config.model_copy(deep=True)
        instance_sut.default_headers["X-Correlation-ID"] = ctx.correlation_id
        turbulence_engine = TurbulenceEngine(scenario.turbulence, seed_value)

        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)
        passed = True
        error: str | None = None

        try:
            async with httpx.AsyncClient() as client:
                for step_index, action in enumerate(scenario.flow):
                    observation, context_dict = await _execute_action(
                        action=action,
                        context=context_dict,
                        sut_config=instance_sut,
                        template_engine=template_engine,
                        client=client,
                        turbulence_engine=turbulence_engine,
                    )
                    if isinstance(action, (HttpAction, WaitAction)):
                        _update_last_response(context_dict, observation)

                    artifact_store.write_step(
                        instance_id=ctx.instance_id,
                        correlation_id=ctx.correlation_id,
                        step_index=step_index,
                        step_name=action.name,
                        step_type=action.type,
                        observation=observation,
                    )

                    if isinstance(action, AssertAction):
                        _write_assertion(
                            artifact_store,
                            ctx.instance_id,
                            ctx.correlation_id,
                            step_index,
                            context_dict,
                        )

                    if not observation.ok:
                        passed = False
                        if scenario.stop_when.any_action_fails:
                            break

                final_offset = len(scenario.flow)
                for assertion_index, assertion in enumerate(scenario.assertions):
                    observation, context_dict = await _execute_assertion(
                        assertion=assertion,
                        context=context_dict,
                        template_engine=template_engine,
                    )

                    _write_assertion(
                        artifact_store,
                        ctx.instance_id,
                        ctx.correlation_id,
                        final_offset + assertion_index,
                        context_dict,
                    )

                    if not observation.ok:
                        passed = False
                        if scenario.stop_when.any_assertion_fails:
                            break
        except Exception as exc:
            passed = False
            error = str(exc)

        completed_at = datetime.now(timezone.utc)
        duration_ms = (time.perf_counter() - start_time) * 1000

        artifact_store.write_instance(
            instance_id=ctx.instance_id,
            correlation_id=ctx.correlation_id,
            scenario_id=scenario.id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            passed=passed,
            entry_data=entry_data,
            error=error,
        )

        return InstanceResult(
            instance_id=ctx.instance_id,
            correlation_id=ctx.correlation_id,
            scenario_id=scenario.id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            passed=passed,
            error=error,
        )

    try:
        await executor.execute(instances, execute_instance)
    finally:
        artifact_store.finalize()

    executor.print_summary()
    return 0


def _pick_scenario(
    scenarios: list[Scenario],
    seed_value: int,
    instance_index: int,
) -> Scenario:
    if len(scenarios) == 1:
        return scenarios[0]
    rng = random.Random(seed_value + instance_index)  # noqa: S311
    return rng.choice(scenarios)


async def _execute_action(
    *,
    action: Action,
    context: dict[str, Any],
    sut_config: SUTConfig,
    template_engine: TemplateEngine,
    client: httpx.AsyncClient,
    turbulence_engine: TurbulenceEngine,
) -> tuple[Observation, dict[str, Any]]:
    rendered_action = _render_action(action, context, template_engine)

    if isinstance(rendered_action, HttpAction):
        runner = HttpActionRunner(
            action=rendered_action,
            sut_config=sut_config,
            client=client,
        )
        policy = turbulence_engine.resolve_policy(
            service=rendered_action.service,
            action=rendered_action.name,
        )
        if policy is not None:
            return await turbulence_engine.apply(
                policy=policy,
                action_name=rendered_action.name,
                service_name=rendered_action.service,
                instance_id=str(context.get("instance_id", "")),
                context=context,
                execute=lambda: runner.execute(context),
            )
        return await runner.execute(context)
    if isinstance(rendered_action, WaitAction):
        runner = WaitActionRunner(
            action=rendered_action,
            sut_config=sut_config,
            client=client,
        )
        return await runner.execute(context)
    if isinstance(rendered_action, AssertAction):
        runner = AssertActionRunner(action=rendered_action)
        return await runner.execute(context)

    raise ValueError(f"Unknown action type: {type(action)}")


async def _execute_assertion(
    *,
    assertion: Assertion,
    context: dict[str, Any],
    template_engine: TemplateEngine,
) -> tuple[Observation, dict[str, Any]]:
    assert_action = AssertAction(
        name=assertion.name,
        type="assert",
        expect=assertion.expect,
    )
    rendered_action = _render_action(assert_action, context, template_engine)
    runner = AssertActionRunner(action=rendered_action)
    return await runner.execute(context)


def _render_action(
    action: Action,
    context: dict[str, Any],
    template_engine: TemplateEngine,
) -> Action:
    action_dict = action.model_dump()
    rendered_dict = template_engine.render_dict(action_dict, context)

    if isinstance(action, HttpAction):
        return HttpAction(**rendered_dict)
    if isinstance(action, WaitAction):
        return WaitAction(**rendered_dict)
    if isinstance(action, AssertAction):
        return AssertAction(**rendered_dict)


def _update_last_response(context: dict[str, Any], observation: Observation) -> None:
    context["last_response"] = {
        "status_code": getattr(observation, "status_code", None),
        "headers": getattr(observation, "headers", {}),
        "body": getattr(observation, "body", None),
    }


def _write_assertion(
    artifact_store: ArtifactStore,
    instance_id: str,
    correlation_id: str,
    step_index: int,
    context: dict[str, Any],
) -> None:
    last_assertion = context.get("_last_assertion")
    if not last_assertion:
        return

    assertion_result = AssertionResult.model_validate(last_assertion)
    artifact_store.write_assertion(
        instance_id=instance_id,
        correlation_id=correlation_id,
        step_index=step_index,
        assertion_result=assertion_result,
    )
