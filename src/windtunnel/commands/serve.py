"""Serve command for running the Web UI server."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()


def serve(
    runs_dir: Path = typer.Option(
        Path("runs"),
        "--runs-dir",
        "-d",
        help="Directory containing run artifacts",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to run the server on",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    static_dir: Path | None = typer.Option(
        None,
        "--static-dir",
        help="Directory containing built frontend files (for production)",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Serve the Windtunnel Web UI.

    Starts a local server that provides:
    - A REST API for accessing run data
    - The web-based dashboard (if static files are provided)

    Example:
        windtunnel serve --runs-dir runs/ --port 8000
    """
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Error: uvicorn is required for the serve command.[/red]\n"
            "Install it with: pip install uvicorn"
        )
        raise typer.Exit(code=1)

    from windtunnel.api.main import create_app

    console.print()
    console.print("[bold blue]Windtunnel Web UI[/bold blue]")
    console.print(f"  Runs directory: {runs_dir}")
    console.print(f"  API server: http://{host}:{port}")
    if static_dir:
        console.print(f"  Static files: {static_dir}")
    else:
        console.print("  [dim]Frontend: Run 'npm run dev' in ui/ for development[/dim]")
    console.print()

    app = create_app(runs_dir=runs_dir, static_dir=static_dir)
    uvicorn.run(app, host=host, port=port)
