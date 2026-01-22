# FEAT-021: FastAPI Backend for Artifact Reading

## Overview

Create a FastAPI backend that reads Windtunnel JSONL artifacts and exposes them via REST API endpoints. This enables the Web UI to access run data without direct filesystem access.

## Dependencies

- FEAT-008 (Artifact Storage) - Reads from existing JSONL format

## Acceptance Criteria

### API Setup
- [ ] Create FastAPI application in `src/windtunnel/api/`
- [ ] Configure CORS for local development (localhost:5173)
- [ ] Add API to CLI as `windtunnel serve` command
- [ ] Serve frontend static files in production mode

### Endpoints

#### Run List
- [ ] `GET /api/runs` - List all runs
  - Returns: run ID, SUT name, scenarios, timestamps, stats summary
  - Sorted by: most recent first
  - Supports: `?limit=N` query parameter

#### Run Detail
- [ ] `GET /api/runs/:runId` - Get run details
  - Returns: manifest, aggregated stats, scenario breakdown
  - Includes: pass rate, duration, error count

#### Instance List
- [ ] `GET /api/runs/:runId/instances` - List instances for a run
  - Returns: paginated list of instances with status
  - Supports: `?status=failed` filter, `?page=N&limit=M` pagination

#### Instance Detail
- [ ] `GET /api/runs/:runId/instances/:instanceId` - Get instance timeline
  - Returns: all steps with observations, assertions, turbulence data

### Service Layer
- [ ] Create `ArtifactReaderService` that:
  - Discovers runs in `runs/` directory
  - Parses manifest.json for run metadata
  - Streams JSONL files for instances/steps
  - Caches frequently accessed data

### Error Handling
- [ ] Return 404 for missing runs/instances
- [ ] Return 500 with error details for parsing failures
- [ ] Include correlation IDs in error responses

## Technical Notes

### API Response Schemas
```python
class RunSummary(BaseModel):
    id: str
    sut_name: str
    scenarios: list[str]
    started_at: datetime
    completed_at: datetime | None
    stats: RunStats

class RunStats(BaseModel):
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    duration_ms: float

class InstanceSummary(BaseModel):
    instance_id: str
    correlation_id: str
    scenario_id: str
    passed: bool | None
    duration_ms: float
    error: str | None
```

### CLI Integration
```python
# In cli.py
@app.command()
def serve(
    runs_dir: Path = Option(Path("runs")),
    port: int = Option(8000),
    host: str = Option("127.0.0.1"),
):
    """Serve the Windtunnel Web UI."""
    import uvicorn
    from windtunnel.api.main import create_app
    
    app = create_app(runs_dir=runs_dir)
    uvicorn.run(app, host=host, port=port)
```

## Estimated Complexity

Medium (2-3 days)

## Definition of Done

- [ ] `windtunnel serve` starts API server on localhost:8000
- [ ] `/api/runs` returns list of available runs
- [ ] `/api/runs/:runId` returns run details with stats
- [ ] `/api/runs/:runId/instances` returns paginated instances
- [ ] `/api/runs/:runId/instances/:instanceId` returns full timeline
- [ ] All endpoints have OpenAPI documentation
- [ ] Unit tests for ArtifactReaderService
