"""FastAPI application for Turbulence Web UI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from turbulence.api.routes.runs import router as runs_router
from turbulence.api.routes.stream import router as stream_router


def create_app(
    runs_dir: Path = Path("runs"), static_dir: Path | None = None
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        runs_dir: Directory containing run artifacts.
        static_dir: Optional directory containing built frontend files.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Turbulence API",
        description="API for Turbulence workflow testing framework",
        version="0.1.0",
    )

    # CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store runs_dir in app state for access in routes
    app.state.runs_dir = runs_dir

    # Include API routes
    app.include_router(runs_router, prefix="/api")
    app.include_router(stream_router, prefix="/api")

    # Serve static files if provided (production mode)
    if static_dir and static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app
