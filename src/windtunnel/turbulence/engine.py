"""Turbulence engine for injecting latency, timeouts, and retries."""

from __future__ import annotations

import asyncio
import hashlib
import random
from typing import Any

from windtunnel.models.observation import Observation
from windtunnel.turbulence.config import TurbulenceConfig, TurbulencePolicy


class TurbulenceEngine:
    """Apply deterministic turbulence injections for HTTP actions."""

    def __init__(self, config: TurbulenceConfig | None, seed: int) -> None:
        self._config = config
        self._seed = seed

    def is_enabled(self) -> bool:
        """Return True if turbulence is enabled."""
        return self._config is not None

    def resolve_policy(self, *, service: str, action: str) -> TurbulencePolicy | None:
        """Resolve a turbulence policy for a specific service and action."""
        if self._config is None:
            return None
        return self._config.resolve(service=service, action=action)

    async def apply(
        self,
        *,
        policy: TurbulencePolicy,
        action_name: str,
        service_name: str,
        instance_id: str,
        context: dict[str, Any],
        execute: Any,
    ) -> tuple[Observation, dict[str, Any]]:
        """Apply turbulence policy around an HTTP action execution."""
        retry_count = policy.retry_count or 0
        attempts = 1 + retry_count
        turbulence_info: dict[str, Any] = {
            "service": service_name,
            "action": action_name,
            "retry_count": retry_count,
            "timeout_after_ms": policy.timeout_after_ms,
            "latency_ms": None,
            "attempts": [],
        }

        last_observation: Observation | None = None
        last_context: dict[str, Any] | None = None

        for attempt in range(attempts):
            injected_latency = self._pick_latency(
                policy,
                instance_id=instance_id,
                action_name=action_name,
                service_name=service_name,
                attempt=attempt,
            )
            if injected_latency is not None:
                turbulence_info["latency_ms"] = injected_latency
                await asyncio.sleep(injected_latency / 1000)

            timeout_after = policy.timeout_after_ms
            try:
                if timeout_after is not None:
                    observation, updated_context = await asyncio.wait_for(
                        execute(),
                        timeout=timeout_after / 1000,
                    )
                else:
                    observation, updated_context = await execute()
            except asyncio.TimeoutError:
                observation = Observation(
                    ok=False,
                    status_code=None,
                    latency_ms=float(timeout_after or 0),
                    headers={},
                    body=None,
                    errors=[f"Injected timeout after {timeout_after}ms"],
                    action_name=action_name,
                )
                updated_context = dict(context)

            turbulence_info["attempts"].append(
                {
                    "ok": observation.ok,
                    "status_code": observation.status_code,
                    "latency_ms": observation.latency_ms,
                    "injected_latency_ms": injected_latency,
                    "errors": observation.errors,
                }
            )
            last_observation = observation
            last_context = updated_context

        if last_observation is None or last_context is None:
            raise RuntimeError("Turbulence execution failed to produce a result")

        last_observation.turbulence = turbulence_info
        return last_observation, last_context

    def _pick_latency(
        self,
        policy: TurbulencePolicy,
        *,
        instance_id: str,
        action_name: str,
        service_name: str,
        attempt: int,
    ) -> int | None:
        if policy.latency_ms is None:
            return None

        seed = self._derive_seed(
            instance_id=instance_id,
            action_name=action_name,
            service_name=service_name,
            attempt=attempt,
        )
        rng = random.Random(seed)  # noqa: S311
        return rng.randint(policy.latency_ms.min, policy.latency_ms.max)

    def _derive_seed(
        self,
        *,
        instance_id: str,
        action_name: str,
        service_name: str,
        attempt: int,
    ) -> int:
        payload = f"{self._seed}:{instance_id}:{service_name}:{action_name}:{attempt}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
