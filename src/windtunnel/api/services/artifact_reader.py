"""Artifact reader service for accessing run data."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RunStats:
    """Aggregated statistics for a run."""

    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    duration_ms: float


@dataclass
class RunSummary:
    """Summary information for a run."""

    id: str
    sut_name: str
    scenarios: list[str]
    started_at: datetime
    completed_at: datetime | None
    stats: RunStats


@dataclass
class InstanceSummary:
    """Summary information for an instance."""

    instance_id: str
    correlation_id: str
    scenario_id: str
    passed: bool | None
    duration_ms: float
    error: str | None


@dataclass
class StepObservation:
    """Observation data for a step."""

    ok: bool
    status_code: int | None
    latency_ms: float
    headers: dict[str, str]
    body: dict | list | None
    errors: list[str]
    turbulence: dict | None = None


@dataclass
class Step:
    """Step data for an instance."""

    index: int
    name: str
    type: str
    observation: StepObservation


@dataclass
class InstanceDetail:
    """Detailed information for an instance."""

    instance_id: str
    correlation_id: str
    scenario_id: str
    passed: bool | None
    duration_ms: float
    entry: dict
    steps: list[Step]


class ArtifactReaderService:
    """Service for reading Windtunnel run artifacts."""

    def __init__(self, runs_dir: Path) -> None:
        """Initialize the artifact reader.

        Args:
            runs_dir: Directory containing run artifacts.
        """
        self.runs_dir = runs_dir

    def list_runs(self, limit: int = 50) -> list[RunSummary]:
        """List all available runs.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of run summaries, sorted by most recent first.
        """
        runs: list[RunSummary] = []

        if not self.runs_dir.exists():
            return runs

        for run_path in sorted(self.runs_dir.iterdir(), reverse=True):
            if not run_path.is_dir():
                continue

            manifest_path = run_path / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                summary = self._read_run_summary(run_path)
                runs.append(summary)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

            if len(runs) >= limit:
                break

        return runs

    def get_run(self, run_id: str) -> RunSummary | None:
        """Get details for a specific run.

        Args:
            run_id: The run ID.

        Returns:
            Run summary or None if not found.
        """
        run_path = self.runs_dir / run_id
        if not run_path.exists():
            return None

        try:
            return self._read_run_summary(run_path)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def list_instances(
        self,
        run_id: str,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> list[InstanceSummary]:
        """List instances for a run.

        Args:
            run_id: The run ID.
            status: Optional filter (passed, failed, errors).
            page: Page number (1-indexed).
            limit: Items per page.

        Returns:
            List of instance summaries.
        """
        run_path = self.runs_dir / run_id
        instances_path = run_path / "instances.jsonl"

        if not instances_path.exists():
            return []

        instances: list[InstanceSummary] = []

        with instances_path.open() as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    instance = InstanceSummary(
                        instance_id=data.get("instance_id", ""),
                        correlation_id=data.get("correlation_id", ""),
                        scenario_id=data.get("scenario_id", ""),
                        passed=data.get("passed"),
                        duration_ms=data.get("duration_ms", 0),
                        error=data.get("error"),
                    )

                    # Apply filter
                    if status == "passed" and not instance.passed:
                        continue
                    if status == "failed" and instance.passed:
                        continue
                    if status == "errors" and not instance.error:
                        continue

                    instances.append(instance)
                except (json.JSONDecodeError, KeyError):
                    continue

        # Paginate
        start = (page - 1) * limit
        end = start + limit
        return instances[start:end]

    def get_instance(self, run_id: str, instance_id: str) -> InstanceDetail | None:
        """Get detailed information for a specific instance.

        Args:
            run_id: The run ID.
            instance_id: The instance ID.

        Returns:
            Instance detail or None if not found.
        """
        run_path = self.runs_dir / run_id

        # Find instance in instances.jsonl
        instances_path = run_path / "instances.jsonl"
        instance_data: dict | None = None

        if instances_path.exists():
            with instances_path.open() as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("instance_id") == instance_id:
                            instance_data = data
                            break
                    except json.JSONDecodeError:
                        continue

        if instance_data is None:
            return None

        # Load steps from steps.jsonl
        steps_path = run_path / "steps.jsonl"
        steps: list[Step] = []

        if steps_path.exists():
            with steps_path.open() as f:
                step_index = 0
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("instance_id") == instance_id:
                            obs_data = data.get("observation", {})
                            observation = StepObservation(
                                ok=obs_data.get("ok", False),
                                status_code=obs_data.get("status_code"),
                                latency_ms=obs_data.get("latency_ms", 0),
                                headers=obs_data.get("headers", {}),
                                body=obs_data.get("body"),
                                errors=obs_data.get("errors", []),
                                turbulence=obs_data.get("turbulence"),
                            )
                            step = Step(
                                index=step_index,
                                name=data.get("action_name", f"step_{step_index}"),
                                type=data.get("action_type", "unknown"),
                                observation=observation,
                            )
                            steps.append(step)
                            step_index += 1
                    except (json.JSONDecodeError, KeyError):
                        continue

        return InstanceDetail(
            instance_id=instance_data.get("instance_id", ""),
            correlation_id=instance_data.get("correlation_id", ""),
            scenario_id=instance_data.get("scenario_id", ""),
            passed=instance_data.get("passed"),
            duration_ms=instance_data.get("duration_ms", 0),
            entry=instance_data.get("entry", {}),
            steps=steps,
        )

    def _read_run_summary(self, run_path: Path) -> RunSummary:
        """Read run summary from manifest and compute stats.

        Args:
            run_path: Path to the run directory.

        Returns:
            Run summary with computed stats.
        """
        manifest_path = run_path / "manifest.json"

        with manifest_path.open() as f:
            manifest = json.load(f)

        # Compute stats from instances
        instances_path = run_path / "instances.jsonl"
        total = 0
        passed = 0
        failed = 0
        errors = 0
        total_duration = 0.0

        if instances_path.exists():
            with instances_path.open() as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        total += 1
                        total_duration += data.get("duration_ms", 0)
                        if data.get("error"):
                            errors += 1
                        elif data.get("passed"):
                            passed += 1
                        else:
                            failed += 1
                    except json.JSONDecodeError:
                        continue

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        stats = RunStats(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            pass_rate=pass_rate,
            duration_ms=total_duration,
        )

        started_at = datetime.fromisoformat(
            manifest.get("started_at", datetime.now().isoformat())
        )
        completed_at_str = manifest.get("completed_at")
        completed_at = (
            datetime.fromisoformat(completed_at_str) if completed_at_str else None
        )

        return RunSummary(
            id=run_path.name,
            sut_name=manifest.get("sut_name", "unknown"),
            scenarios=manifest.get("scenarios", []),
            started_at=started_at,
            completed_at=completed_at,
            stats=stats,
        )
