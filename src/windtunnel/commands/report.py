"""Report command for generating HTML reports from run artifacts."""

from pathlib import Path

import typer
from rich.console import Console

from windtunnel.report import HTMLReportGenerator

console = Console()


def report(
    run_id: str = typer.Option(
        ...,
        "--run-id",
        "-r",
        help="The run ID to generate a report for",
    ),
    runs_dir: Path = typer.Option(
        Path("runs"),
        "--runs-dir",
        "-d",
        help="Directory containing run artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for the report (default: runs/<run_id>/report.html)",
        resolve_path=True,
    ),
) -> None:
    """Generate an HTML report from run artifacts.

    Reads the JSONL artifacts from a completed run and generates a self-contained
    HTML report with pass rates, failing assertions, and service breakdowns.

    Example:
        windtunnel report --run-id run_20240115_001
    """
    run_path = runs_dir / run_id
    if not run_path.exists():
        console.print(f"[red]Error: Run '{run_id}' not found in {runs_dir}[/red]")
        raise typer.Exit(code=1)

    output_path = output or (run_path / "report.html")

    console.print("[bold blue]Windtunnel Report[/bold blue]")
    console.print(f"  Run ID: {run_id}")
    console.print(f"  Run path: {run_path}")
    console.print(f"  Output: {output_path}")
    console.print()

    try:
        generator = HTMLReportGenerator(run_path)
        result_path = generator.generate(output_path)
        console.print(f"[green]Report generated successfully: {result_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(code=1) from None

    raise typer.Exit(code=0)
