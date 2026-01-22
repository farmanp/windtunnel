"""Configuration models for variation engine."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VariationType(str, Enum):
    """Type of parameter variation."""

    CHOICE = "choice"
    RANGE = "range"


class ParameterVariation(BaseModel):
    """Configuration for a single parameter variation."""

    model_config = {"extra": "forbid"}

    type: VariationType = Field(
        ...,
        description="Type of variation: choice (pick from list) or range (random value)",
    )
    values: list[Any] | None = Field(
        default=None,
        description="List of values to choose from (for choice type)",
    )
    min: float | None = Field(
        default=None,
        description="Minimum value for range (for range type)",
    )
    max: float | None = Field(
        default=None,
        description="Maximum value for range (for range type)",
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate configuration based on type."""
        if self.type == VariationType.CHOICE:
            if not self.values:
                raise ValueError("Choice variation requires 'values' list")
        elif self.type == VariationType.RANGE:
            if self.min is None or self.max is None:
                raise ValueError("Range variation requires 'min' and 'max'")
            if self.min >= self.max:
                raise ValueError("Range 'min' must be less than 'max'")


class ToggleVariation(BaseModel):
    """Configuration for a journey toggle (boolean flag with probability)."""

    model_config = {"extra": "forbid"}

    name: str = Field(
        ...,
        description="Name of the toggle (e.g., 'apply_coupon')",
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability (0.0-1.0) that this toggle is enabled",
    )


class TimingConfig(BaseModel):
    """Configuration for timing variations."""

    model_config = {"extra": "forbid"}

    jitter_ms: dict[str, int] | None = Field(
        default=None,
        description="Random jitter added to each step in milliseconds {min: X, max: Y}",
    )
    step_delay_ms: dict[str, int] | None = Field(
        default=None,
        description="Delay between steps in milliseconds {min: X, max: Y}",
    )

    def model_post_init(self, __context: Any) -> None:
        """Validate timing ranges."""
        if self.jitter_ms:
            if "min" not in self.jitter_ms or "max" not in self.jitter_ms:
                raise ValueError("jitter_ms requires 'min' and 'max' keys")
            if self.jitter_ms["min"] < 0:
                raise ValueError("jitter_ms 'min' must be >= 0")
            if self.jitter_ms["min"] >= self.jitter_ms["max"]:
                raise ValueError("jitter_ms 'min' must be less than 'max'")

        if self.step_delay_ms:
            if "min" not in self.step_delay_ms or "max" not in self.step_delay_ms:
                raise ValueError("step_delay_ms requires 'min' and 'max' keys")
            if self.step_delay_ms["min"] < 0:
                raise ValueError("step_delay_ms 'min' must be >= 0")
            if self.step_delay_ms["min"] >= self.step_delay_ms["max"]:
                raise ValueError("step_delay_ms 'min' must be less than 'max'")


class VariationConfig(BaseModel):
    """Complete variation configuration for a scenario."""

    model_config = {"extra": "forbid"}

    parameters: dict[str, ParameterVariation] = Field(
        default_factory=dict,
        description="Named parameters to vary (e.g., cart_quantity, locale)",
    )
    toggles: list[ToggleVariation] = Field(
        default_factory=list,
        description="Boolean toggles with activation probability",
    )
    timing: TimingConfig | None = Field(
        default=None,
        description="Timing variation configuration",
    )
