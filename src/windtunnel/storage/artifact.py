"""Artifact storage for run persistence using JSONL files."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from windtunnel.models.assertion_result import AssertionResult
from windtunnel.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunConfig,
    RunManifest,
    RunSummary,
    StepRecord,
)
from windtunnel.models.observation import Observation
from windtunnel.storage.jsonl import JSONLWriter


class ArtifactStore:
    """Manages artifact storage for a single test run.

    Creates a directory structure under runs/<run_id>/ containing:
    - manifest.json: Run metadata and configuration
    - instances.jsonl: One line per instance execution
    - steps.jsonl: One line per step observation
    - assertions.jsonl: One line per assertion result
    - summary.json: Final aggregated statistics
    - artifacts/: Per-instance raw data (optional)

    All JSONL files are written with immediate flush for durability.
    """

    def __init__(
        self,
        run_id: str,
        base_path: Path | None = None,
        sut_name: str = "",
        scenario_ids: list[str] | None = None,
        seed: int | None = None,
        config: RunConfig | None = None,
    ) -> None:
        """Initialize the artifact store for a run.

        Args:
            run_id: Unique identifier for this run.
            base_path: Base directory for runs (default: ./runs).
            sut_name: Name of the system under test.
            scenario_ids: List of scenario IDs being executed.
            seed: Random seed for reproducibility.
            config: Run configuration snapshot.
        """
        self._run_id = run_id
        self._base_path = base_path or Path("runs")
        self._run_path = self._base_path / run_id
        self._sut_name = sut_name
        self._scenario_ids = scenario_ids or []
        self._seed = seed
        self._config = config or RunConfig()

        # File paths
        self._manifest_path = self._run_path / "manifest.json"
        self._instances_path = self._run_path / "instances.jsonl"
        self._steps_path = self._run_path / "steps.jsonl"
        self._assertions_path = self._run_path / "assertions.jsonl"
        self._summary_path = self._run_path / "summary.json"
        self._artifacts_path = self._run_path / "artifacts"

        # JSONL writers (opened lazily)
        self._instances_writer: JSONLWriter | None = None
        self._steps_writer: JSONLWriter | None = None
        self._assertions_writer: JSONLWriter | None = None

        # Tracking for summary
        self._started_at: datetime | None = None
        self._total_instances = 0
        self._pass_count = 0
        self._fail_count = 0
        self._error_count = 0
        self._total_steps = 0
        self._total_assertions = 0
        self._assertions_passed = 0
        self._assertions_failed = 0
        self._is_initialized = False

    @property
    def run_id(self) -> str:
        """Return the run ID."""
        return self._run_id

    @property
    def run_path(self) -> Path:
        """Return the path to the run directory."""
        return self._run_path

    @property
    def manifest_path(self) -> Path:
        """Return the path to manifest.json."""
        return self._manifest_path

    @property
    def instances_path(self) -> Path:
        """Return the path to instances.jsonl."""
        return self._instances_path

    @property
    def steps_path(self) -> Path:
        """Return the path to steps.jsonl."""
        return self._steps_path

    @property
    def assertions_path(self) -> Path:
        """Return the path to assertions.jsonl."""
        return self._assertions_path

    @property
    def summary_path(self) -> Path:
        """Return the path to summary.json."""
        return self._summary_path

    @property
    def artifacts_path(self) -> Path:
        """Return the path to the artifacts directory."""
        return self._artifacts_path

    def initialize(self) -> "ArtifactStore":
        """Initialize the run directory and write the manifest.

        Creates the directory structure and writes manifest.json.
        Must be called before writing any artifacts.

        Returns:
            Self for method chaining.
        """
        if self._is_initialized:
            return self

        # Create directory structure
        self._run_path.mkdir(parents=True, exist_ok=True)
        self._artifacts_path.mkdir(parents=True, exist_ok=True)

        # Record start time
        self._started_at = datetime.now(UTC)

        # Write manifest
        manifest = RunManifest(
            run_id=self._run_id,
            timestamp=self._started_at,
            sut_name=self._sut_name,
            scenario_ids=self._scenario_ids,
            seed=self._seed,
            config=self._config,
        )
        with self._manifest_path.open("w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        # Open JSONL writers
        self._instances_writer = JSONLWriter(self._instances_path).open()
        self._steps_writer = JSONLWriter(self._steps_path).open()
        self._assertions_writer = JSONLWriter(self._assertions_path).open()

        self._is_initialized = True
        return self

    def write_instance(
        self,
        instance_id: str,
        correlation_id: str,
        scenario_id: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration_ms: float | None = None,
        passed: bool | None = None,
        entry_data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Write an instance record to instances.jsonl.

        Args:
            instance_id: Unique identifier for this instance.
            correlation_id: Correlation ID for request tracing.
            scenario_id: ID of the scenario being executed.
            started_at: When the instance started (default: now).
            completed_at: When the instance completed.
            duration_ms: Total duration in milliseconds.
            passed: Whether all assertions passed.
            entry_data: Entry context data.
            error: Error message if instance failed.
        """
        self._ensure_initialized()

        record = InstanceRecord(
            instance_id=instance_id,
            run_id=self._run_id,
            correlation_id=correlation_id,
            scenario_id=scenario_id,
            started_at=started_at or datetime.now(UTC),
            completed_at=completed_at,
            duration_ms=duration_ms,
            passed=passed,
            entry_data=entry_data or {},
            error=error,
        )

        if self._instances_writer is not None:
            self._instances_writer.write(record)

        # Update tracking
        self._total_instances += 1
        if passed is True:
            self._pass_count += 1
        elif passed is False:
            self._fail_count += 1
        if error is not None:
            self._error_count += 1

    def write_step(
        self,
        instance_id: str,
        correlation_id: str,
        step_index: int,
        step_name: str,
        step_type: str,
        observation: Observation | dict[str, Any],
        timestamp: datetime | None = None,
    ) -> None:
        """Write a step record to steps.jsonl.

        Args:
            instance_id: Instance ID this step belongs to.
            correlation_id: Correlation ID for request tracing.
            step_index: Zero-based index of this step.
            step_name: Name of the step/action.
            step_type: Type of action (http, wait, assert).
            observation: Observation data from step execution.
            timestamp: When the step executed (default: now).
        """
        self._ensure_initialized()

        if isinstance(observation, Observation):
            obs_dict = observation.model_dump()
        else:
            obs_dict = observation

        record = StepRecord(
            instance_id=instance_id,
            run_id=self._run_id,
            correlation_id=correlation_id,
            step_index=step_index,
            step_name=step_name,
            step_type=step_type,
            timestamp=timestamp or datetime.now(UTC),
            observation=obs_dict,
        )

        if self._steps_writer is not None:
            self._steps_writer.write(record)

        self._total_steps += 1

    def write_assertion(
        self,
        instance_id: str,
        correlation_id: str,
        step_index: int,
        assertion_result: AssertionResult | None = None,
        assertion_name: str = "",
        passed: bool = False,
        expected: Any = None,
        actual: Any = None,
        message: str = "",
        timestamp: datetime | None = None,
    ) -> None:
        """Write an assertion record to assertions.jsonl.

        Can accept either an AssertionResult object or individual fields.

        Args:
            instance_id: Instance ID this assertion belongs to.
            correlation_id: Correlation ID for request tracing.
            step_index: Index of the step that produced this assertion.
            assertion_result: AssertionResult object (optional).
            assertion_name: Name of the assertion (if not using assertion_result).
            passed: Whether the assertion passed (if not using assertion_result).
            expected: Expected value (if not using assertion_result).
            actual: Actual value (if not using assertion_result).
            message: Result message (if not using assertion_result).
            timestamp: When the assertion was evaluated (default: now).
        """
        self._ensure_initialized()

        if assertion_result is not None:
            assertion_name = assertion_result.name
            passed = assertion_result.passed
            expected = assertion_result.expected
            actual = assertion_result.actual
            message = assertion_result.message

        record = AssertionRecord(
            instance_id=instance_id,
            run_id=self._run_id,
            correlation_id=correlation_id,
            step_index=step_index,
            assertion_name=assertion_name,
            passed=passed,
            expected=expected,
            actual=actual,
            message=message,
            timestamp=timestamp or datetime.now(UTC),
        )

        if self._assertions_writer is not None:
            self._assertions_writer.write(record)

        # Update tracking
        self._total_assertions += 1
        if passed:
            self._assertions_passed += 1
        else:
            self._assertions_failed += 1

    def write_instance_artifact(
        self,
        instance_id: str,
        filename: str,
        data: dict[str, Any] | str,
    ) -> Path:
        """Write a raw artifact file for a specific instance.

        Args:
            instance_id: Instance ID this artifact belongs to.
            filename: Name of the artifact file.
            data: Data to write (dict for JSON, str for raw).

        Returns:
            Path to the written artifact file.
        """
        self._ensure_initialized()

        # Create instance artifact directory
        instance_dir = self._artifacts_path / instance_id
        instance_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = instance_dir / filename

        with artifact_path.open("w", encoding="utf-8") as f:
            if isinstance(data, dict):
                json.dump(data, f, indent=2, default=str)
            else:
                f.write(data)

        return artifact_path

    def finalize(self) -> RunSummary:
        """Finalize the run and write summary.json.

        Closes all JSONL writers and writes the final summary.

        Returns:
            The generated RunSummary.
        """
        self._ensure_initialized()

        # Close JSONL writers
        if self._instances_writer is not None:
            self._instances_writer.close()
            self._instances_writer = None

        if self._steps_writer is not None:
            self._steps_writer.close()
            self._steps_writer = None

        if self._assertions_writer is not None:
            self._assertions_writer.close()
            self._assertions_writer = None

        # Calculate duration
        completed_at = datetime.now(UTC)
        duration_ms = 0.0
        if self._started_at is not None:
            duration_ms = (completed_at - self._started_at).total_seconds() * 1000

        # Calculate pass rate
        pass_rate = 0.0
        if self._total_instances > 0:
            pass_rate = (self._pass_count / self._total_instances) * 100

        # Create and write summary
        summary = RunSummary(
            run_id=self._run_id,
            completed_at=completed_at,
            total_instances=self._total_instances,
            pass_count=self._pass_count,
            fail_count=self._fail_count,
            error_count=self._error_count,
            pass_rate=pass_rate,
            duration_ms=duration_ms,
            total_steps=self._total_steps,
            total_assertions=self._total_assertions,
            assertions_passed=self._assertions_passed,
            assertions_failed=self._assertions_failed,
        )

        with self._summary_path.open("w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))

        return summary

    def _ensure_initialized(self) -> None:
        """Ensure the store has been initialized.

        Raises:
            RuntimeError: If initialize() has not been called.
        """
        if not self._is_initialized:
            raise RuntimeError(
                "ArtifactStore must be initialized before writing. "
                "Call initialize() first."
            )

    def __enter__(self) -> "ArtifactStore":
        """Context manager entry - initializes the store."""
        return self.initialize()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit - finalizes the store."""
        self.finalize()
