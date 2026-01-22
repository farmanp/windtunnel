"""Parallel execution engine for running workflow instances concurrently."""

from __future__ import annotations

import asyncio
import signal
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

if TYPE_CHECKING:
    from turbulence.storage.artifact import ArtifactStore

# Default parallelism if not specified
DEFAULT_PARALLELISM = 10


@dataclass
class InstanceResult:
    """Result of a single workflow instance execution."""

    instance_id: str
    correlation_id: str
    scenario_id: str
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    passed: bool | None = None
    error: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExecutionStats:
    """Statistics for the overall execution run."""

    total_instances: int = 0
    completed: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    cancelled: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_ms(self) -> float:
        """Total duration in milliseconds."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds() * 1000

    @property
    def pass_rate(self) -> float:
        """Pass rate as a percentage."""
        if self.completed == 0:
            return 0.0
        return (self.passed / self.completed) * 100


# Type alias for workflow execution function
WorkflowExecutor = Callable[[int], Coroutine[Any, Any, InstanceResult]]


class ParallelExecutor:
    """Executes workflow instances in parallel with configurable concurrency.

    This executor manages the parallel execution of workflow instances using
    asyncio semaphores for concurrency control. It provides:
    - Configurable parallelism via --parallel flag
    - Rich progress display with completion %, current/total, and ETA
    - Graceful Ctrl+C handling that completes in-flight instances
    - Partial result saving on cancellation
    """

    def __init__(
        self,
        parallelism: int = DEFAULT_PARALLELISM,
        console: Console | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        """Initialize the parallel executor.

        Args:
            parallelism: Maximum number of concurrent workflow instances.
            console: Rich console for output. If not provided, a new one is created.
            artifact_store: Optional artifact store for saving results.
        """
        self._parallelism = max(1, parallelism)
        self._console = console or Console()
        self._artifact_store = artifact_store

        # Execution state
        self._semaphore: asyncio.Semaphore | None = None
        self._cancel_requested = False
        self._results: list[InstanceResult] = []
        self._stats = ExecutionStats()
        self._lock = asyncio.Lock()

        # Progress tracking
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None

    @property
    def parallelism(self) -> int:
        """Return the configured parallelism level."""
        return self._parallelism

    @property
    def stats(self) -> ExecutionStats:
        """Return the current execution statistics."""
        return self._stats

    @property
    def results(self) -> list[InstanceResult]:
        """Return the collected instance results."""
        return self._results.copy()

    @property
    def cancel_requested(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._cancel_requested

    def request_cancel(self) -> None:
        """Request graceful cancellation of the execution.

        In-flight instances will complete but no new instances will start.
        """
        self._cancel_requested = True
        self._console.print(
            "\n[yellow]Cancellation requested. "
            "Waiting for in-flight instances to complete...[/yellow]"
        )

    async def execute(
        self,
        total_instances: int,
        workflow_executor: WorkflowExecutor,
    ) -> ExecutionStats:
        """Execute workflow instances in parallel.

        Args:
            total_instances: Total number of instances to execute.
            workflow_executor: Async function that executes a single instance.
                Takes instance index (0-based) and returns InstanceResult.

        Returns:
            ExecutionStats with the final execution statistics.
        """
        self._reset_state(total_instances)

        # Set up signal handler for graceful cancellation
        original_handler = signal.getsignal(signal.SIGINT)

        def signal_handler(sig: int, frame: Any) -> None:  # noqa: ARG001
            self.request_cancel()

        # Install signal handler
        try:
            signal.signal(signal.SIGINT, signal_handler)
        except ValueError:
            # Signal handlers can only be set in the main thread
            pass

        try:
            await self._run_with_progress(total_instances, workflow_executor)
        finally:
            # Restore original signal handler
            try:
                signal.signal(signal.SIGINT, original_handler)
            except (ValueError, TypeError):
                pass

            self._stats.completed_at = datetime.now(timezone.utc)

        return self._stats

    async def _run_with_progress(
        self,
        total_instances: int,
        workflow_executor: WorkflowExecutor,
    ) -> None:
        """Run execution with progress display.

        Args:
            total_instances: Total number of instances to execute.
            workflow_executor: Async function that executes a single instance.
        """
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console,
            refresh_per_second=10,
        )

        with self._progress:
            self._task_id = self._progress.add_task(
                "Running instances",
                total=total_instances,
            )

            # Create tasks for all instances
            tasks = []
            for i in range(total_instances):
                task = asyncio.create_task(self._execute_instance(i, workflow_executor))
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        self._progress = None
        self._task_id = None

    async def _execute_instance(
        self,
        instance_index: int,
        workflow_executor: WorkflowExecutor,
    ) -> InstanceResult | None:
        """Execute a single instance with semaphore control.

        Args:
            instance_index: Zero-based index of the instance.
            workflow_executor: Async function that executes the instance.

        Returns:
            InstanceResult or None if cancelled before starting.
        """
        # Check for cancellation before acquiring semaphore
        if self._cancel_requested:
            async with self._lock:
                self._stats.cancelled += 1
                if self._progress and self._task_id is not None:
                    self._progress.update(self._task_id, advance=1)
            return None

        # Acquire semaphore to limit concurrency
        semaphore = self._semaphore
        if semaphore is None:
            return None

        async with semaphore:
            # Check again after acquiring (in case cancelled while waiting)
            if self._cancel_requested:  # noqa: SIM102
                async with self._lock:  # type: ignore[unreachable]
                    self._stats.cancelled += 1
                    if self._progress and self._task_id is not None:
                        self._progress.update(self._task_id, advance=1)
                return None

            try:
                result = await workflow_executor(instance_index)
                await self._record_result(result)
                return result
            except Exception as e:
                import traceback
                logger.debug(f"Unexpected exception in instance {instance_index}: {traceback.format_exc()}")

                # Create error result for unexpected exceptions
                error_result = InstanceResult(
                    instance_id=f"error_{instance_index}",
                    correlation_id=f"corr_{instance_index}",
                    scenario_id="unknown",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_ms=0.0,
                    passed=False,
                    error=str(e),
                )
                await self._record_result(error_result)
                return error_result

    async def _record_result(self, result: InstanceResult) -> None:
        """Record an instance result and update statistics.

        Args:
            result: The instance result to record.
        """
        async with self._lock:
            self._results.append(result)
            self._stats.completed += 1

            if result.error:
                self._stats.errors += 1
            elif result.passed is True:
                self._stats.passed += 1
            elif result.passed is False:
                self._stats.failed += 1

            # Update progress bar
            if self._progress and self._task_id is not None:
                self._progress.update(self._task_id, advance=1)

            # Write to artifact store if available
            if self._artifact_store:
                self._artifact_store.write_instance(
                    instance_id=result.instance_id,
                    correlation_id=result.correlation_id,
                    scenario_id=result.scenario_id,
                    started_at=result.started_at,
                    completed_at=result.completed_at,
                    duration_ms=result.duration_ms,
                    passed=result.passed,
                    error=result.error,
                )

    def _reset_state(self, total_instances: int) -> None:
        """Reset internal state for a new execution run.

        Args:
            total_instances: Total number of instances to execute.
        """
        self._cancel_requested = False
        self._results = []
        self._stats = ExecutionStats(
            total_instances=total_instances,
            started_at=datetime.now(timezone.utc),
        )
        self._semaphore = asyncio.Semaphore(self._parallelism)

    def print_summary(self) -> None:
        """Print a summary of the execution results."""
        stats = self._stats

        self._console.print()
        self._console.print("[bold]Execution Summary[/bold]")
        self._console.print(f"  Total instances: {stats.total_instances}")
        self._console.print(f"  Completed: {stats.completed}")
        self._console.print(f"  Passed: [green]{stats.passed}[/green]")
        self._console.print(f"  Failed: [red]{stats.failed}[/red]")
        if stats.errors > 0:
            self._console.print(f"  Errors: [red]{stats.errors}[/red]")
        if stats.cancelled > 0:
            self._console.print(f"  Cancelled: [yellow]{stats.cancelled}[/yellow]")
        self._console.print(f"  Pass rate: {stats.pass_rate:.1f}%")
        self._console.print(f"  Duration: {stats.duration_ms:.0f}ms")


async def run_parallel(
    total_instances: int,
    workflow_executor: WorkflowExecutor,
    parallelism: int = DEFAULT_PARALLELISM,
    console: Console | None = None,
    artifact_store: ArtifactStore | None = None,
) -> tuple[ExecutionStats, list[InstanceResult]]:
    """Convenience function to run parallel execution.

    Args:
        total_instances: Total number of instances to execute.
        workflow_executor: Async function that executes a single instance.
        parallelism: Maximum number of concurrent workflow instances.
        console: Rich console for output.
        artifact_store: Optional artifact store for saving results.

    Returns:
        Tuple of (ExecutionStats, list of InstanceResults).
    """
    executor = ParallelExecutor(
        parallelism=parallelism,
        console=console,
        artifact_store=artifact_store,
    )

    stats = await executor.execute(total_instances, workflow_executor)
    return stats, executor.results
