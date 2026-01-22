"""Tests for parallel execution engine (FEAT-011)."""

import asyncio
from datetime import datetime, timezone

import pytest

from windtunnel.engine import ExecutionStats, ParallelExecutor
from windtunnel.engine.executor import InstanceResult


@pytest.mark.asyncio
async def test_parallel_executor_limits_concurrency() -> None:
    """Executor should not exceed configured parallelism."""
    total_instances = 20
    parallelism = 5
    active = 0
    max_active = 0
    lock = asyncio.Lock()

    async def workflow(instance_index: int) -> InstanceResult:
        nonlocal active, max_active
        async with lock:
            active += 1
            max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        async with lock:
            active -= 1
        now = datetime.now(timezone.utc)
        return InstanceResult(
            instance_id=f"inst_{instance_index}",
            correlation_id=f"corr_{instance_index}",
            scenario_id="test",
            started_at=now,
            completed_at=now,
            duration_ms=1.0,
            passed=True,
        )

    executor = ParallelExecutor(parallelism=parallelism)
    stats = await executor.execute(total_instances, workflow)

    assert max_active <= parallelism
    assert stats.completed == total_instances
    assert stats.cancelled == 0


@pytest.mark.asyncio
async def test_parallel_executor_cancels_new_instances() -> None:
    """Cancellation should stop new instances from starting."""
    total_instances = 10
    parallelism = 2
    active = 0
    lock = asyncio.Lock()
    release_event = asyncio.Event()

    async def workflow(instance_index: int) -> InstanceResult:
        nonlocal active
        async with lock:
            active += 1
        await release_event.wait()
        async with lock:
            active -= 1
        now = datetime.now(timezone.utc)
        return InstanceResult(
            instance_id=f"inst_{instance_index}",
            correlation_id=f"corr_{instance_index}",
            scenario_id="test",
            started_at=now,
            completed_at=now,
            duration_ms=1.0,
            passed=True,
        )

    executor = ParallelExecutor(parallelism=parallelism)

    async def run_executor() -> ExecutionStats:
        return await executor.execute(total_instances, workflow)

    task = asyncio.create_task(run_executor())

    while True:
        async with lock:
            if active >= parallelism:
                break
        await asyncio.sleep(0.001)

    executor.request_cancel()
    release_event.set()
    stats = await task

    assert stats.completed <= parallelism
    assert stats.cancelled >= total_instances - stats.completed
