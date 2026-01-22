"""Configuration models for turbulence injection."""

from pydantic import BaseModel, ConfigDict, Field


class LatencyConfig(BaseModel):
    """Latency injection configuration in milliseconds."""

    model_config = ConfigDict(extra="forbid")

    min: int = Field(..., ge=0, description="Minimum latency in ms")
    max: int = Field(..., ge=0, description="Maximum latency in ms")


class TurbulencePolicy(BaseModel):
    """Turbulence settings for a scope (global/service/action)."""

    model_config = ConfigDict(extra="forbid")

    latency_ms: LatencyConfig | None = Field(
        default=None,
        description="Latency injection settings",
    )
    timeout_after_ms: int | None = Field(
        default=None,
        ge=1,
        description="Force timeout after this many milliseconds",
    )
    retry_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of retries to inject",
    )


class TurbulenceConfig(BaseModel):
    """Top-level turbulence configuration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    global_policy: TurbulencePolicy | None = Field(
        default=None,
        alias="global",
        description="Global turbulence settings",
    )
    services: dict[str, TurbulencePolicy] = Field(
        default_factory=dict,
        description="Per-service turbulence settings",
    )
    actions: dict[str, TurbulencePolicy] = Field(
        default_factory=dict,
        description="Per-action turbulence settings",
    )

    def resolve(self, *, service: str, action: str) -> TurbulencePolicy | None:
        """Resolve the effective turbulence policy for a service/action."""
        policies = [
            self.global_policy,
            self.services.get(service),
            self.actions.get(action),
        ]
        merged = TurbulencePolicy()
        has_policy = False

        for policy in policies:
            if policy is None:
                continue
            has_policy = True
            if policy.latency_ms is not None:
                merged.latency_ms = policy.latency_ms
            if policy.timeout_after_ms is not None:
                merged.timeout_after_ms = policy.timeout_after_ms
            if policy.retry_count is not None:
                merged.retry_count = policy.retry_count

        return merged if has_policy else None
