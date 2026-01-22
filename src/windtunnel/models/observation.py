"""Observation model for capturing action execution results."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Observation(BaseModel):
    """Captures the result of an action execution.

    An observation records all relevant data about an action's execution,
    including success/failure status, timing, response data, and any errors.
    """

    model_config = ConfigDict(extra="forbid")

    ok: bool = Field(
        ...,
        description="Whether the action completed successfully",
    )
    status_code: int | None = Field(
        default=None,
        description="HTTP status code if applicable",
    )
    latency_ms: float = Field(
        ...,
        description="Execution time in milliseconds",
        ge=0,
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Response headers",
    )
    body: Any = Field(
        default=None,
        description="Response body (parsed JSON or raw text)",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of error messages if any occurred",
    )
    action_name: str = Field(
        default="",
        description="Name of the action that produced this observation",
    )
    turbulence: dict[str, Any] | None = Field(
        default=None,
        description="Injected turbulence details, if any",
    )
