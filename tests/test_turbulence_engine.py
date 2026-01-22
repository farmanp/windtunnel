"""Tests for turbulence engine (FEAT-012)."""

import asyncio
from typing import Any

import pytest

from windtunnel.models.observation import Observation
from windtunnel.turbulence.config import (
    LatencyConfig,
    TurbulenceConfig,
    TurbulencePolicy,
)
from windtunnel.turbulence.engine import TurbulenceEngine


@pytest.mark.asyncio
async def test_latency_injection_records_latency() -> None:
    """Injected latency is recorded on observations."""
    config = TurbulenceConfig(
        global_policy=TurbulencePolicy(latency_ms=LatencyConfig(min=1, max=1))
    )
    engine = TurbulenceEngine(config, seed=123)
    policy = config.resolve(service="api", action="get_user")

    context = {"instance_id": "inst_1"}

    async def execute() -> tuple[Observation, dict[str, Any]]:
        return (
            Observation(
                ok=True, status_code=200, latency_ms=1, action_name="get_user"
            ),
            context,
        )

    observation, _ = await engine.apply(
        policy=policy,
        action_name="get_user",
        service_name="api",
        instance_id="inst_1",
        context=context,
        execute=execute,
    )

    assert observation.turbulence is not None
    assert observation.turbulence["attempts"][0]["injected_latency_ms"] == 1


@pytest.mark.asyncio
async def test_timeout_injection_forces_failure() -> None:
    """Injected timeout aborts execution."""
    config = TurbulenceConfig(
        global_policy=TurbulencePolicy(timeout_after_ms=5)
    )
    engine = TurbulenceEngine(config, seed=123)
    policy = config.resolve(service="api", action="slow_call")
    context = {"instance_id": "inst_2"}

    async def execute() -> tuple[Observation, dict[str, Any]]:
        await asyncio.sleep(0.05)
        return (
            Observation(
                ok=True, status_code=200, latency_ms=50, action_name="slow_op"
            ),
            context,
        )

    observation, _ = await engine.apply(
        policy=policy,
        action_name="slow_call",
        service_name="api",
        instance_id="inst_2",
        context=context,
        execute=execute,
    )

    assert observation.ok is False
    assert "Injected timeout" in observation.errors[0]


@pytest.mark.asyncio
async def test_retry_storm_repeats_attempts() -> None:
    """Retry count triggers multiple attempts."""
    config = TurbulenceConfig(
        global_policy=TurbulencePolicy(retry_count=2)
    )
    engine = TurbulenceEngine(config, seed=123)
    policy = config.resolve(service="api", action="retry_call")
    context = {"instance_id": "inst_3"}
    calls = {"count": 0}

    async def execute() -> tuple[Observation, dict[str, Any]]:
        calls["count"] += 1
        return (
            Observation(
                ok=False, status_code=500, latency_ms=1, action_name="fail_op"
            ),
            dict(context),
        )

    observation, _ = await engine.apply(
        policy=policy,
        action_name="retry_call",
        service_name="api",
        instance_id="inst_3",
        context=context,
        execute=execute,
    )

    assert calls["count"] == 3
    assert len(observation.turbulence["attempts"]) == 3


@pytest.mark.asyncio
async def test_deterministic_latency_with_seed() -> None:
    """Latency injection is deterministic with the same seed and inputs."""
    config = TurbulenceConfig(
        global_policy=TurbulencePolicy(latency_ms=LatencyConfig(min=10, max=20))
    )
    engine = TurbulenceEngine(config, seed=999)
    policy = config.resolve(service="api", action="deterministic")
    context = {"instance_id": "inst_4"}

    async def execute() -> tuple[Observation, dict[str, Any]]:
        return (
            Observation(ok=True, status_code=200, latency_ms=1, action_name="det"),
            context,
        )

    obs_a, _ = await engine.apply(
        policy=policy,
        action_name="deterministic",
        service_name="api",
        instance_id="inst_4",
        context=context,
        execute=execute,
    )
    obs_b, _ = await engine.apply(
        policy=policy,
        action_name="deterministic",
        service_name="api",
        instance_id="inst_4",
        context=context,
        execute=execute,
    )

    latency_a = obs_a.turbulence["attempts"][0]["injected_latency_ms"]
    latency_b = obs_b.turbulence["attempts"][0]["injected_latency_ms"]
    assert latency_a == latency_b
