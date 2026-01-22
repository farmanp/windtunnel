"""AssertionResult model for assertion evaluation results."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssertionResult(BaseModel):
    """Result of an assertion evaluation.

    Captures the outcome of a single assertion including name, pass/fail status,
    and detailed information about expected vs actual values for debugging.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Name of the assertion for reporting",
    )
    passed: bool = Field(
        ...,
        description="Whether the assertion passed",
    )
    expected: Any = Field(
        default=None,
        description="The expected value",
    )
    actual: Any = Field(
        default=None,
        description="The actual value that was evaluated",
    )
    message: str = Field(
        default="",
        description="Human-readable message describing the result",
    )
    path: str | None = Field(
        default=None,
        description="The JSONPath or context path that was evaluated",
    )
    comparison: str | None = Field(
        default=None,
        description="The type of comparison (equals, contains, status_code)",
    )
