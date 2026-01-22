"""Routes for run management."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, Request

from windtunnel.api.services.artifact_reader import ArtifactReaderService

router = APIRouter(tags=["runs"])


def get_reader(request: Request) -> ArtifactReaderService:
    """Get artifact reader from app state."""
    return ArtifactReaderService(request.app.state.runs_dir)


@router.get("/runs")
def list_runs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
) -> dict:
    """List all available runs.

    Args:
        request: FastAPI request object.
        limit: Maximum number of runs to return.

    Returns:
        Dictionary with list of runs.
    """
    reader = get_reader(request)
    runs = reader.list_runs(limit=limit)
    return {"runs": [asdict(run) for run in runs]}


@router.get("/runs/{run_id}")
def get_run(request: Request, run_id: str) -> dict:
    """Get details for a specific run.

    Args:
        request: FastAPI request object.
        run_id: The run ID.

    Returns:
        Run details.

    Raises:
        HTTPException: If run not found.
    """
    reader = get_reader(request)
    run = reader.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return asdict(run)


@router.get("/runs/{run_id}/instances")
def list_instances(
    request: Request,
    run_id: str,
    status: str | None = Query(default=None, pattern="^(passed|failed|errors)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict:
    """List instances for a run.

    Args:
        request: FastAPI request object.
        run_id: The run ID.
        status: Optional filter (passed, failed, errors).
        page: Page number (1-indexed).
        limit: Items per page.

    Returns:
        Dictionary with list of instances.
    """
    reader = get_reader(request)
    instances = reader.list_instances(run_id, status=status, page=page, limit=limit)
    return {"instances": [asdict(inst) for inst in instances]}


@router.get("/runs/{run_id}/instances/{instance_id}")
def get_instance(request: Request, run_id: str, instance_id: str) -> dict:
    """Get detailed information for a specific instance.

    Args:
        request: FastAPI request object.
        run_id: The run ID.
        instance_id: The instance ID.

    Returns:
        Instance details.

    Raises:
        HTTPException: If instance not found.
    """
    reader = get_reader(request)
    instance = reader.get_instance(run_id, instance_id)
    if instance is None:
        raise HTTPException(
            status_code=404,
            detail=f"Instance '{instance_id}' not found in run '{run_id}'",
        )

    # Convert dataclasses to dict, handling nested structures
    result = asdict(instance)
    return result
