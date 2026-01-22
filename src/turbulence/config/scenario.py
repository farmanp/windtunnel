"""Scenario configuration models for workflow definitions."""

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from turbulence.pressure.config import TurbulenceConfig
from turbulence.variation.config import VariationConfig


class Expectation(BaseModel):
    """Expectation for assertions and wait conditions."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status_code: int | None = Field(
        default=None,
        description="Expected HTTP status code",
    )
    jsonpath: str | None = Field(
        default=None,
        description="JSONPath expression to extract value for comparison",
    )
    context_path: str | None = Field(
        default=None,
        description="Context key to extract value for comparison",
    )
    equals: Any | None = Field(
        default=None,
        description="Expected value must equal this",
    )
    contains: Any | None = Field(
        default=None,
        description="Expected value must contain this",
    )
    json_schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON Schema to validate response against (inline or $ref)",
        alias="schema",
    )
    expression: str | None = Field(
        default=None,
        description="Python expression to evaluate against response/context",
    )


class RetryConfig(BaseModel):
    """Configuration for automatic action retries."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(
        default=3,
        description="Maximum total attempts (1 initial + retries)",
        gt=0,
    )
    on_status: list[int] = Field(
        default_factory=list,
        description="List of HTTP status codes to retry on (e.g., [500, 502])",
    )
    on_timeout: bool = Field(
        default=False,
        description="Retry on request timeouts",
    )
    on_connection_error: bool = Field(
        default=False,
        description="Retry on connection errors",
    )
    backoff: Literal["fixed", "exponential"] = Field(
        default="exponential",
        description="Backoff strategy",
    )
    delay_ms: int = Field(
        default=1000,
        description="Delay for fixed backoff (ms)",
        ge=0,
    )
    base_delay_ms: int = Field(
        default=100,
        description="Initial delay for exponential backoff (ms)",
        ge=0,
    )
    max_delay_ms: int = Field(
        default=10000,
        description="Maximum delay for exponential backoff (ms)",
        ge=0,
    )


class HttpAction(BaseModel):
    """HTTP action configuration for making requests."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(..., description="Unique name for this action")
    type: Literal["http"] = Field("http", description="Action type discriminator")
    service: str = Field(..., description="Target service name from SUT config")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(..., description="Request path (can use {{templates}})")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers for this request",
    )
    query: dict[str, str] = Field(
        default_factory=dict,
        description="Query parameters",
    )
    body: dict[str, Any] | list[Any] | None = Field(
        default=None,
        alias="json",
        description="JSON body (can use {{templates}})",
    )
    extract: dict[str, str] = Field(
        default_factory=dict,
        description="Values to extract from response using JSONPath",
    )
    retry: RetryConfig | None = Field(
        default=None,
        description="Retry policy for this action",
    )


class WaitAction(BaseModel):
    """Wait action configuration for polling until a condition is met."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique name for this action")
    type: Literal["wait"] = Field("wait", description="Action type discriminator")
    service: str = Field(..., description="Target service name from SUT config")
    method: str = Field(default="GET", description="HTTP method for polling")
    path: str = Field(..., description="Request path to poll")
    interval_seconds: float = Field(
        default=1.0,
        description="Seconds between poll attempts",
        gt=0,
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Maximum seconds to wait before failing",
        gt=0,
    )
    expect: Expectation = Field(
        ...,
        description="Condition that must be met for wait to succeed",
    )


class AssertAction(BaseModel):
    """Assert action configuration for inline workflow assertions."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique name for this assertion")
    type: Literal["assert"] = Field("assert", description="Action type discriminator")
    expect: Expectation = Field(
        ...,
        description="Expectation to validate",
    )


# Discriminated union for action types
Action = Annotated[
    HttpAction | WaitAction | AssertAction,
    Field(discriminator="type"),
]


class Assertion(BaseModel):
    """Final assertion to run after workflow completes."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique name for this assertion")
    type: Literal["assert"] = Field(
        default="assert",
        description="Assertion type",
    )
    expect: Expectation = Field(
        ...,
        description="Expectation to validate",
    )


class StopCondition(BaseModel):
    """Conditions that trigger workflow termination."""

    model_config = ConfigDict(extra="forbid")

    any_assertion_fails: bool = Field(
        default=False,
        description="Stop immediately if any assertion fails",
    )
    any_action_fails: bool = Field(
        default=False,
        description="Stop immediately if any action fails",
    )


class EntryContext(BaseModel):
    """Entry context defining initial data for a workflow instance."""

    model_config = ConfigDict(extra="allow")

    seed_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial seed data available as {{entry.seed_data.*}}",
    )


class Scenario(BaseModel):
    """Complete scenario definition for a workflow simulation.

    A scenario defines a complete user journey from entry context through
    a series of actions to final assertions.
    """

    model_config = ConfigDict(extra="forbid")

    _source_path: Path | None = PrivateAttr(default=None)

    id: str = Field(
        ...,
        description="Unique identifier for this scenario",
        min_length=1,
    )
    description: str = Field(
        default="",
        description="Human-readable description of the scenario",
    )
    entry: EntryContext = Field(
        default_factory=EntryContext,
        description="Initial context for workflow instances",
    )
    flow: list[Action] = Field(
        default_factory=list,
        description="Ordered list of actions to execute",
    )
    assertions: list[Assertion] = Field(
        default_factory=list,
        description="Final assertions to run after flow completes",
    )
    stop_when: StopCondition = Field(
        default_factory=StopCondition,
        description="Conditions that trigger early termination",
    )
    max_steps: int = Field(
        default=100,
        description="Maximum number of steps before forced termination",
        gt=0,
    )
    turbulence: TurbulenceConfig | None = Field(
        default=None,
        description="Optional turbulence configuration for this scenario",
    )
    variation: VariationConfig | None = Field(
        default=None,
        description="Optional variation configuration for input fuzzing",
    )

    @property
    def source_path(self) -> Path | None:
        """Return the source path this scenario was loaded from, if known."""
        return self._source_path
