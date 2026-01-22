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

from turbulence.actions.assert_ import AssertActionRunner
from turbulence.config.loader import load_scenarios, load_sut
from turbulence.config.scenario import (
    AssertAction,
    Assertion,
    Scenario,
)
from turbulence.config.sut import SUTConfig
from turbulence.engine.context import WorkflowContext
from turbulence.engine.executor import (
    DEFAULT_PARALLELISM,
    InstanceResult,
    ParallelExecutor,
)
from turbulence.engine.scenario_runner import ScenarioRunner
from turbulence.engine.template import TemplateEngine
from turbulence.models.assertion_result import AssertionResult
from turbulence.models.manifest import RunConfig
from turbulence.models.observation import Observation
from turbulence.pressure.engine import TurbulenceEngine
from turbulence.storage.artifact import ArtifactStore

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
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-P",
        help="Environment profile to activate (e.g. 'staging', 'prod')",
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
        turbulence run --sut sut.yaml --scenarios scenarios/ --n 1000 --parallel 50
    """
    exit_code = asyncio.run(
        _run_instances(
            sut=sut,
            scenarios_dir=scenarios,
            instances=n,
            parallelism=parallel,
            seed=seed,
            profile=profile,
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
    profile: str | None,
    output_dir: Path,
) -> int:
    sut_config = load_sut(sut, profile=profile)
    scenario_list = load_scenarios(scenarios_dir)
    seed_value = seed if seed is not None else random.SystemRandom().randint(1, 2**31)

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    run_config = RunConfig(seed=seed_value, concurrency=parallelism)

    console.print("[bold blue]Turbulence Run[/bold blue]")
    console.print(f"  Run ID: {run_id}")
    console.print(f"  SUT config: {sut}")
    console.print(f"  Profile: {profile or sut_config.default_profile or '(default)'}")
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

        scenario_runner = ScenarioRunner(
            template_engine=template_engine,
            sut_config=instance_sut,
            turbulence_engine=turbulence_engine,
        )

        try:
            async with httpx.AsyncClient() as client:
                async for step_index, action, observation, context_dict in scenario_runner.execute_flow(
                    scenario, context_dict, client
                ):
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
            import traceback
            from logging import getLogger
            getLogger(__name__).debug(f"Unexpected exception in instance execution: {traceback.format_exc()}")
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




async def _execute_assertion(
    *,
    assertion: Assertion,
    context: dict[str, Any],
    template_engine: TemplateEngine,
) -> tuple[Observation, dict[str, Any]]:
    """Execute a final assertion (not part of the flow)."""
    assert_action = AssertAction(
        name=assertion.name,
        type="assert",
        expect=assertion.expect,
    )
    # Render templates inline
    action_dict = assert_action.model_dump()
    rendered_dict = template_engine.render_dict(action_dict, context)
    rendered_action = AssertAction(**rendered_dict)
    
    runner = AssertActionRunner(action=rendered_action)
    return await runner.execute(context)


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
