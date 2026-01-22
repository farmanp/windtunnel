"""Replay engine for re-executing workflow instances."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from turbulence.actions.assert_ import AssertActionRunner
from turbulence.actions.http import HttpActionRunner
from turbulence.actions.wait import WaitActionRunner
from turbulence.config.scenario import (
    Action,
    AssertAction,
    HttpAction,
    Scenario,
    WaitAction,
)
from turbulence.config.sut import SUTConfig
from turbulence.engine.context import WorkflowContext
from turbulence.engine.template import TemplateEngine
from turbulence.models.observation import Observation


class InstanceNotFoundError(Exception):
    """Raised when an instance cannot be found in run artifacts."""

    def __init__(self, run_id: str, instance_id: str, run_path: Path) -> None:
        self.run_id = run_id
        self.instance_id = instance_id
        self.run_path = run_path
        super().__init__(
            f"Instance '{instance_id}' not found in run '{run_id}' at {run_path}"
        )


class ScenarioNotFoundError(Exception):
    """Raised when a scenario cannot be found."""

    def __init__(self, scenario_id: str, scenarios_path: Path) -> None:
        self.scenario_id = scenario_id
        self.scenarios_path = scenarios_path
        super().__init__(f"Scenario '{scenario_id}' not found at {scenarios_path}")


@dataclass
class InstanceData:
    """Data for a stored workflow instance."""

    instance_id: str
    run_id: str
    correlation_id: str
    scenario_id: str
    seed: int
    entry: dict[str, Any]
    original_results: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstanceData":
        """Create InstanceData from a dictionary."""
        return cls(
            instance_id=data["instance_id"],
            run_id=data["run_id"],
            correlation_id=data["correlation_id"],
            scenario_id=data["scenario_id"],
            seed=data.get("seed", 0),
            entry=data.get("entry", {}),
            original_results=data.get("results", []),
        )


@dataclass
class StepResult:
    """Result of a single step execution during replay."""

    step_number: int
    action_name: str
    action_type: str
    observation: Observation
    original_observation: dict[str, Any] | None = None
    has_difference: bool = False
    difference_details: str | None = None


@dataclass
class ReplayResult:
    """Complete result of a replay execution."""

    instance_id: str
    correlation_id: str
    scenario_id: str
    success: bool
    steps: list[StepResult] = field(default_factory=list)
    error: str | None = None


class ReplayEngine:
    """Engine for replaying workflow instances.

    Loads instance data from stored artifacts and re-executes
    the workflow with the same seed, context, and correlation ID.
    """

    def __init__(
        self,
        runs_dir: Path,
        scenarios_dir: Path | None = None,
        sut_config: SUTConfig | None = None,
    ) -> None:
        """Initialize the replay engine.

        Args:
            runs_dir: Directory containing run artifacts.
            scenarios_dir: Directory containing scenario definitions.
            sut_config: System under test configuration.
        """
        self.runs_dir = runs_dir
        self.scenarios_dir = scenarios_dir
        self.sut_config = sut_config
        self.template_engine = TemplateEngine()

    def load_instance(self, run_id: str, instance_id: str) -> InstanceData:
        """Load instance data from artifacts.

        Args:
            run_id: The run ID containing the instance.
            instance_id: The instance ID to load.

        Returns:
            InstanceData with the stored instance information.

        Raises:
            InstanceNotFoundError: If the instance cannot be found.
        """
        run_path = self.runs_dir / run_id
        instances_file = run_path / "instances.jsonl"

        if not instances_file.exists():
            raise InstanceNotFoundError(run_id, instance_id, run_path)

        with instances_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("instance_id") == instance_id:
                        return InstanceData.from_dict(data)
                except json.JSONDecodeError:
                    continue

        raise InstanceNotFoundError(run_id, instance_id, run_path)

    def load_scenario(self, scenario_id: str) -> Scenario:
        """Load a scenario definition.

        Args:
            scenario_id: The scenario ID to load.

        Returns:
            The Scenario object.

        Raises:
            ScenarioNotFoundError: If the scenario cannot be found.
        """
        if self.scenarios_dir is None:
            raise ScenarioNotFoundError(scenario_id, Path())

        # Try common extensions
        for ext in [".yaml", ".yml", ".json"]:
            scenario_path = self.scenarios_dir / f"{scenario_id}{ext}"
            if scenario_path.exists():
                import yaml

                with scenario_path.open() as f:
                    if ext == ".json":
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f)
                scenario = Scenario.model_validate(data)
                scenario._source_path = scenario_path
                return scenario

        raise ScenarioNotFoundError(scenario_id, self.scenarios_dir)

    def create_context_from_instance(
        self, instance_data: InstanceData
    ) -> WorkflowContext:
        """Create a WorkflowContext from stored instance data.

        Args:
            instance_data: The stored instance data.

        Returns:
            WorkflowContext initialized with the instance's original context.
        """
        ctx = WorkflowContext(
            run_id=instance_data.run_id,
            instance_id=instance_data.instance_id,
            correlation_id=instance_data.correlation_id,
        )
        ctx.set_entry(instance_data.entry)
        return ctx

    async def execute_step(
        self,
        action: Action,
        context: dict[str, Any],
        client: httpx.AsyncClient | None = None,
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute a single workflow step.

        Args:
            action: The action to execute.
            context: Current execution context.
            client: Optional HTTP client to use.

        Returns:
            Tuple of (Observation, updated_context).
        """
        # Render templates in action
        rendered_action = self._render_action(action, context)

        if self.sut_config is None:
            raise ValueError("SUT config is required for replay execution")

        if isinstance(rendered_action, HttpAction):
            runner = HttpActionRunner(
                action=rendered_action,
                sut_config=self.sut_config,
                client=client,
            )
            return await runner.execute(context)
        elif isinstance(rendered_action, WaitAction):
            runner = WaitActionRunner(
                action=rendered_action,
                sut_config=self.sut_config,
                client=client,
            )
            return await runner.execute(context)
        elif isinstance(rendered_action, AssertAction):
            runner = AssertActionRunner(action=rendered_action)
            return await runner.execute(context)
        else:
            raise ValueError(f"Unknown action type: {type(action)}")

    def _render_action(self, action: Action, context: dict[str, Any]) -> Action:
        """Render template variables in an action.

        Args:
            action: The action with template variables.
            context: Context for template rendering.

        Returns:
            Action with templates rendered.
        """
        # Convert to dict, render, and reconstruct
        action_dict = action.model_dump()
        rendered_dict = self.template_engine.render_dict(action_dict, context)

        if isinstance(action, HttpAction):
            return HttpAction(**rendered_dict)
        elif isinstance(action, WaitAction):
            return WaitAction(**rendered_dict)
        elif isinstance(action, AssertAction):
            return AssertAction(**rendered_dict)
        else:
            return action

    def _compare_observations(
        self,
        current: Observation,
        original: dict[str, Any] | None,
    ) -> tuple[bool, str | None]:
        """Compare current observation with original.

        Args:
            current: The observation from current replay.
            original: The original observation data (if available).

        Returns:
            Tuple of (has_difference, difference_details).
        """
        if original is None:
            return False, None

        differences = []

        # Compare status codes
        orig_status = original.get("status_code")
        if orig_status != current.status_code:
            differences.append(
                f"status_code: original={orig_status}, replay={current.status_code}"
            )

        # Compare ok status
        orig_ok = original.get("ok")
        if orig_ok != current.ok:
            differences.append(f"ok: original={orig_ok}, replay={current.ok}")

        if differences:
            return True, "; ".join(differences)
        return False, None

    async def replay(
        self,
        run_id: str,
        instance_id: str,
        scenario: Scenario | None = None,
    ) -> ReplayResult:
        """Replay a workflow instance.

        Args:
            run_id: The run ID containing the instance.
            instance_id: The instance ID to replay.
            scenario: Optional pre-loaded scenario (will be loaded if not provided).

        Returns:
            ReplayResult with step-by-step execution results.
        """
        # Load instance data
        try:
            instance_data = self.load_instance(run_id, instance_id)
        except InstanceNotFoundError as e:
            return ReplayResult(
                instance_id=instance_id,
                correlation_id="",
                scenario_id="",
                success=False,
                error=str(e),
            )

        # Load scenario if not provided
        if scenario is None:
            try:
                scenario = self.load_scenario(instance_data.scenario_id)
            except ScenarioNotFoundError as e:
                return ReplayResult(
                    instance_id=instance_id,
                    correlation_id=instance_data.correlation_id,
                    scenario_id=instance_data.scenario_id,
                    success=False,
                    error=str(e),
                )

        # Create context from instance data
        ctx = self.create_context_from_instance(instance_data)
        context_dict = ctx.to_dict()
        if scenario.source_path is not None:
            context_dict["_scenario_path"] = scenario.source_path

        # Add correlation_id to default headers for tracing
        if self.sut_config is not None:
            self.sut_config.default_headers["X-Correlation-ID"] = ctx.correlation_id

        steps: list[StepResult] = []
        success = True

        async with httpx.AsyncClient() as client:
            for step_num, action in enumerate(scenario.flow, start=1):
                # Get original result if available
                original_obs = None
                if step_num <= len(instance_data.original_results):
                    original_obs = instance_data.original_results[step_num - 1]

                try:
                    observation, context_dict = await self.execute_step(
                        action, context_dict, client
                    )
                except Exception as e:
                    observation = Observation(
                        ok=False,
                        latency_ms=0.0,
                        action_name=action.name,
                        errors=[str(e)],
                    )
                    success = False

                # Compare with original
                has_diff, diff_details = self._compare_observations(
                    observation, original_obs
                )

                step_result = StepResult(
                    step_number=step_num,
                    action_name=action.name,
                    action_type=action.type,
                    observation=observation,
                    original_observation=original_obs,
                    has_difference=has_diff,
                    difference_details=diff_details,
                )
                steps.append(step_result)

                if not observation.ok:
                    success = False
                    if scenario.stop_when.any_action_fails:
                        break

        return ReplayResult(
            instance_id=instance_id,
            correlation_id=ctx.correlation_id,
            scenario_id=scenario.id,
            success=success,
            steps=steps,
        )
