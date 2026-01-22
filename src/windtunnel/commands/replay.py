"""Replay command for re-executing specific workflow instances."""

import asyncio
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from windtunnel.config.sut import SUTConfig
from windtunnel.engine.replay import (
    InstanceNotFoundError,
    ReplayEngine,
    ReplayResult,
    StepResult,
)

console = Console()


def _load_sut_config(sut_path: Path) -> SUTConfig:
    """Load SUT configuration from file.

    Args:
        sut_path: Path to SUT configuration file.

    Returns:
        SUTConfig object.
    """
    with sut_path.open() as f:
        data = yaml.safe_load(f)
    return SUTConfig(**data)


def _format_step_result(step: StepResult, verbose: bool) -> None:
    """Format and print a step result.

    Args:
        step: The step result to format.
        verbose: Whether to show detailed output.
    """
    # Determine status icon and color
    if step.observation.ok:
        status_icon = "[green]PASS[/green]"
    else:
        status_icon = "[red]FAIL[/red]"

    # Show difference indicator if there's a difference from original
    diff_indicator = ""
    if step.has_difference:
        diff_indicator = " [yellow](DIFF)[/yellow]"

    # Basic step info
    console.print(
        f"  [{step.step_number}] {step.action_name} "
        f"({step.action_type}) {status_icon}{diff_indicator}"
    )

    if verbose:
        # Show latency
        console.print(f"      Latency: {step.observation.latency_ms:.2f}ms")

        # Show status code if present
        if step.observation.status_code is not None:
            console.print(f"      Status: {step.observation.status_code}")

        # Show errors if any
        if step.observation.errors:
            for error in step.observation.errors:
                console.print(f"      [red]Error: {error}[/red]")

        # Show difference details
        if step.difference_details:
            diff_msg = f"      [yellow]Difference: {step.difference_details}[/yellow]"
            console.print(diff_msg)


def _format_result_table(result: ReplayResult) -> Table:
    """Format replay results as a rich table.

    Args:
        result: The replay result to format.

    Returns:
        Rich Table with step results.
    """
    table = Table(title="Replay Results", show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Action", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Status", width=8)
    table.add_column("Latency", justify="right")
    table.add_column("Diff", width=6)

    for step in result.steps:
        status = "[green]PASS[/green]" if step.observation.ok else "[red]FAIL[/red]"
        diff = "[yellow]YES[/yellow]" if step.has_difference else ""
        latency = f"{step.observation.latency_ms:.1f}ms"

        table.add_row(
            str(step.step_number),
            step.action_name,
            step.action_type,
            status,
            latency,
            diff,
        )

    return table


def _print_summary(result: ReplayResult) -> None:
    """Print a summary panel for the replay result.

    Args:
        result: The replay result to summarize.
    """
    total_steps = len(result.steps)
    passed_steps = sum(1 for s in result.steps if s.observation.ok)
    failed_steps = total_steps - passed_steps
    diff_steps = sum(1 for s in result.steps if s.has_difference)

    if result.success:
        status_color = "green"
        status_text = "SUCCESS"
    else:
        status_color = "red"
        status_text = "FAILED"

    summary_lines = [
        f"Status: [{status_color}]{status_text}[/{status_color}]",
        f"Instance: {result.instance_id}",
        f"Correlation ID: {result.correlation_id}",
        f"Scenario: {result.scenario_id}",
        "",
        f"Steps: {total_steps} total, [green]{passed_steps} passed[/green], "
        f"[red]{failed_steps} failed[/red]",
    ]

    if diff_steps > 0:
        summary_lines.append(
            f"Differences from original: [yellow]{diff_steps}[/yellow]"
        )

    if result.error:
        summary_lines.append(f"[red]Error: {result.error}[/red]")

    console.print(Panel("\n".join(summary_lines), title="Replay Summary"))


async def _run_replay(
    run_id: str,
    instance_id: str,
    runs_dir: Path,
    scenarios_dir: Path | None,
    sut_path: Path | None,
    verbose: bool,
) -> int:
    """Run the replay asynchronously.

    Args:
        run_id: The run ID containing the instance.
        instance_id: The instance ID to replay.
        runs_dir: Directory containing run artifacts.
        scenarios_dir: Directory containing scenario definitions.
        sut_path: Path to SUT configuration file.
        verbose: Whether to show verbose output.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Load SUT config if provided
    sut_config = None
    if sut_path is not None and sut_path.exists():
        try:
            sut_config = _load_sut_config(sut_path)
        except Exception as e:
            console.print(f"[red]Error loading SUT config: {e}[/red]")
            return 1

    # Initialize replay engine
    engine = ReplayEngine(
        runs_dir=runs_dir,
        scenarios_dir=scenarios_dir,
        sut_config=sut_config,
    )

    # Show header
    console.print()
    console.print("[bold blue]Windtunnel Replay[/bold blue]")
    console.print(f"  Run ID: {run_id}")
    console.print(f"  Instance ID: {instance_id}")
    console.print()

    # Load instance to show info before replay
    try:
        instance_data = engine.load_instance(run_id, instance_id)
        console.print(f"  Correlation ID: [cyan]{instance_data.correlation_id}[/cyan]")
        console.print(f"  Scenario: [cyan]{instance_data.scenario_id}[/cyan]")
        console.print()
    except InstanceNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Check if we can actually execute (need SUT config)
    if sut_config is None:
        console.print(
            "[yellow]Warning: No SUT config provided. "
            "Showing instance data only (no re-execution).[/yellow]"
        )
        console.print()
        console.print("[bold]Instance Data:[/bold]")
        console.print(f"  Entry context: {instance_data.entry}")
        console.print(f"  Seed: {instance_data.seed}")
        num_results = len(instance_data.original_results)
        console.print(f"  Original results: {num_results} steps")
        return 0

    # Execute replay
    console.print("[bold]Executing replay...[/bold]")
    console.print()

    result = await engine.replay(run_id, instance_id)

    # Show step-by-step output if verbose
    if verbose:
        console.print("[bold]Step Results:[/bold]")
        for step in result.steps:
            _format_step_result(step, verbose=True)
        console.print()

    # Show results table
    table = _format_result_table(result)
    console.print(table)
    console.print()

    # Show summary
    _print_summary(result)

    return 0 if result.success else 1


def replay(
    run_id: str = typer.Option(
        ...,
        "--run-id",
        "-r",
        help="The run ID containing the instance to replay",
    ),
    instance_id: str = typer.Option(
        ...,
        "--instance-id",
        "-i",
        help="The specific instance ID to replay",
    ),
    runs_dir: Path = typer.Option(
        Path("runs"),
        "--runs-dir",
        "-d",
        help="Directory containing run artifacts",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    scenarios_dir: Path | None = typer.Option(
        None,
        "--scenarios",
        "-c",
        help="Directory containing scenario definitions",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    sut_path: Path | None = typer.Option(
        None,
        "--sut",
        "-s",
        help="Path to SUT configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed step-by-step output",
    ),
) -> None:
    """Replay a specific workflow instance for debugging.

    Loads the instance from stored artifacts and re-executes it with the same
    seed, context, and correlation ID. Useful for debugging failures by
    reproducing the exact conditions of the original run.

    Example:
        windtunnel replay --run-id run_20240115_001 --instance-id inst_042
        windtunnel replay -r run_001 -i inst_042 --sut sut.yaml --scenarios scenarios/
    """
    run_path = runs_dir / run_id
    if not run_path.exists():
        console.print(f"[red]Error: Run '{run_id}' not found in {runs_dir}[/red]")
        raise typer.Exit(code=1)

    exit_code = asyncio.run(
        _run_replay(
            run_id=run_id,
            instance_id=instance_id,
            runs_dir=runs_dir,
            scenarios_dir=scenarios_dir,
            sut_path=sut_path,
            verbose=verbose,
        )
    )
    raise typer.Exit(code=exit_code)
