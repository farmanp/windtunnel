"""Run manifest model for artifact storage metadata."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


class RunConfig(BaseModel):
    """Configuration snapshot for a run."""

    model_config = ConfigDict(extra="allow")

    seed: int | None = Field(
        default=None,
        description="Random seed used for reproducibility",
    )
    concurrency: int = Field(
        default=1,
        description="Number of concurrent instances",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Timeout in seconds for each action",
    )


class RunManifest(BaseModel):
    """Manifest containing metadata about a test run.

    Written to manifest.json at the start of each run.
    Contains all information needed to identify and replay a run.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(
        ...,
        description="Unique identifier for this run",
    )
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp when the run started",
    )
    sut_name: str = Field(
        ...,
        description="Name of the system under test",
    )
    scenario_ids: list[str] = Field(
        default_factory=list,
        description="List of scenario IDs included in this run",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    config: RunConfig = Field(
        default_factory=RunConfig,
        description="Run configuration snapshot",
    )
    windtunnel_version: str = Field(
        default="0.1.0",
        description="Version of windtunnel that created this run",
    )


class InstanceRecord(BaseModel):
    """Record for a single workflow instance execution.

    Written to instances.jsonl, one line per instance.
    """

    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(
        ...,
        description="Unique identifier for this instance",
    )
    run_id: str = Field(
        ...,
        description="Run ID this instance belongs to",
    )
    correlation_id: str = Field(
        ...,
        description="Correlation ID for request tracing",
    )
    scenario_id: str = Field(
        ...,
        description="ID of the scenario being executed",
    )
    started_at: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp when instance started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when instance completed",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Total duration in milliseconds",
    )
    passed: bool | None = Field(
        default=None,
        description="Whether all assertions passed",
    )
    entry_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Entry context data for this instance",
    )
    error: str | None = Field(
        default=None,
        description="Error message if instance failed",
    )


class StepRecord(BaseModel):
    """Record for a single step execution within an instance.

    Written to steps.jsonl, one line per step.
    """

    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(
        ...,
        description="Instance ID this step belongs to",
    )
    run_id: str = Field(
        ...,
        description="Run ID for correlation",
    )
    correlation_id: str = Field(
        ...,
        description="Correlation ID for request tracing",
    )
    step_index: int = Field(
        ...,
        description="Zero-based index of this step in the workflow",
    )
    step_name: str = Field(
        ...,
        description="Name of the step/action",
    )
    step_type: str = Field(
        ...,
        description="Type of action (http, wait, assert)",
    )
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp when step executed",
    )
    observation: dict[str, Any] = Field(
        default_factory=dict,
        description="Observation data from step execution",
    )


class AssertionRecord(BaseModel):
    """Record for a single assertion result.

    Written to assertions.jsonl, one line per assertion.
    """

    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(
        ...,
        description="Instance ID this assertion belongs to",
    )
    run_id: str = Field(
        ...,
        description="Run ID for correlation",
    )
    correlation_id: str = Field(
        ...,
        description="Correlation ID for request tracing",
    )
    step_index: int = Field(
        ...,
        description="Index of the step that produced this assertion",
    )
    assertion_name: str = Field(
        ...,
        description="Name of the assertion",
    )
    passed: bool = Field(
        ...,
        description="Whether the assertion passed",
    )
    expected: Any = Field(
        default=None,
        description="Expected value",
    )
    actual: Any = Field(
        default=None,
        description="Actual value",
    )
    message: str = Field(
        default="",
        description="Human-readable result message",
    )
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp when assertion was evaluated",
    )


class RunSummary(BaseModel):
    """Summary statistics for a completed run.

    Written to summary.json at the end of each run.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(
        ...,
        description="Run ID this summary is for",
    )
    completed_at: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp when run completed",
    )
    total_instances: int = Field(
        default=0,
        description="Total number of instances executed",
    )
    pass_count: int = Field(
        default=0,
        description="Number of instances that passed",
    )
    fail_count: int = Field(
        default=0,
        description="Number of instances that failed",
    )
    error_count: int = Field(
        default=0,
        description="Number of instances with errors",
    )
    pass_rate: float = Field(
        default=0.0,
        description="Percentage of instances that passed (0-100)",
    )
    duration_ms: float = Field(
        default=0.0,
        description="Total run duration in milliseconds",
    )
    total_steps: int = Field(
        default=0,
        description="Total number of steps executed",
    )
    total_assertions: int = Field(
        default=0,
        description="Total number of assertions evaluated",
    )
    assertions_passed: int = Field(
        default=0,
        description="Number of assertions that passed",
    )
    assertions_failed: int = Field(
        default=0,
        description="Number of assertions that failed",
    )
