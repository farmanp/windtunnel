# Turbulence Project Guide

High-performance workflow simulation and testing framework for distributed systems.

## Project Overview

Turbulence enables stress-testing, validation, and analysis of complex distributed systems through:
- Declarative YAML scenarios defining user journeys
- Async execution engine simulating thousands of concurrent workflows
- Deep observability with automatic trace correlation
- Rich HTML reporting and real-time web dashboard

## Architecture

### Core Components

```
src/turbulence/
├── cli.py                    # Typer CLI entry point
├── commands/                 # CLI command implementations
│   ├── run.py               # Execute workflow simulations
│   ├── report.py            # Generate HTML reports
│   ├── replay.py            # Replay specific instances
│   └── serve.py             # Start FastAPI web server
├── config/                   # Configuration loaders
│   ├── sut.py               # System Under Test config (services, URLs, headers)
│   └── scenario.py          # Scenario/flow definitions
├── actions/                  # Action runners (implement BaseAction)
│   ├── http.py              # HTTP requests with extraction
│   ├── wait.py              # Polling with conditions
│   └── assert_.py           # Assertions with JSONPath/expressions
├── engine/                   # Execution infrastructure
│   ├── executor.py          # Parallel execution with semaphore control
│   ├── template.py          # Jinja2 context templating
│   ├── context.py           # Workflow context management
│   └── replay.py            # Instance replay engine
├── storage/                  # Persistence layer
│   ├── artifact.py          # Run/instance artifact management
│   └── jsonl.py             # JSONL file operations
├── validation/               # Data validation
│   └── schema.py            # JSON Schema validation with $ref support
├── evaluation/               # Expression evaluation
│   └── sandbox.py           # AST-based safe expression evaluator
├── report/                   # Report generation
│   └── html.py              # HTML report with Jinja2 templates
├── pressure/                 # Fault injection
│   ├── config.py            # Pressure configuration
│   └── engine.py            # Fault pattern application
├── api/                      # FastAPI backend
│   ├── main.py              # FastAPI app setup
│   ├── routes/              # API endpoints
│   │   ├── runs.py          # Run CRUD operations
│   │   └── stream.py        # WebSocket streaming
│   └── services/            # Business logic
│       └── artifact_reader.py
└── models/                   # Pydantic models
    ├── observation.py       # Action execution results
    ├── assertion_result.py  # Assertion outcomes
    └── manifest.py          # Run/instance metadata

ui/                           # React frontend (Vite + Tailwind)
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Route pages (dashboard, run detail)
│   └── api/                 # API client

docs/                         # Docusaurus documentation site
```

### Key Patterns

**Action Runner Interface**: All actions implement `BaseAction.execute(context) -> Observation`

**Observation Model**: Unified result format with `ok`, `status_code`, `latency_ms`, `headers`, `body`, `errors`

**Context Flow**: SUT config + scenario → template engine → action runners → observations → artifact storage

**Parallel Execution**: `asyncio.Semaphore` controls concurrency, graceful cancellation preserves partial results

**Safe Expressions**: AST validation whitelist prevents code injection while enabling complex assertions

## Technology Stack

- **Python 3.10+**: Core framework
- **Typer**: CLI framework
- **Pydantic v2**: Configuration and validation
- **httpx**: Async HTTP client
- **asyncio**: Concurrent execution
- **Jinja2**: Template rendering
- **jsonpath-ng**: JSONPath extraction
- **jsonschema**: Schema validation
- **Rich**: Terminal formatting
- **FastAPI + Uvicorn**: Web API
- **React + Vite + Tailwind**: Frontend

## Development

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Testing

```bash
pytest                    # Run all tests
pytest tests/test_*.py    # Run specific test file
pytest -k "test_name"     # Run by pattern
```

### Linting

```bash
ruff check src tests      # Check style
ruff format src tests     # Format code
mypy src                  # Type checking
```

### CLI Commands

```bash
turbulence run --sut sut.yaml --scenarios scenarios/ --parallel 10 --count 100
turbulence report --run-id <id>
turbulence replay --run-id <id> --instance-id <id>
turbulence serve --port 8000
```

## Project Status

**Completed (Batches 0-5, 8):**
- CLI scaffold with all commands
- SUT and scenario configuration
- HTTP, Wait, Assert action runners
- Context templating engine
- JSONL artifact storage
- HTML report generation
- Replay engine
- Parallel execution engine
- Pressure (fault injection)
- JSON Schema validation
- Safe expression evaluator
- FastAPI backend
- React dashboard (run list, run detail, instance timeline)
- Real-time WebSocket streaming
- Environment variable support
- Environment profiles
- Retry policies
- Enhanced report aggregations

**Upcoming (Batch 6-7, 9-10):**
- CI gating with thresholds
- Deterministic variation engine
- SQLite backend option
- Branching flows
- Web UI enhancements (Scenario visualizer, live progress)

See `tickets/TICKET-GRAPH.md` for full roadmap.

## Configuration Examples

### SUT Config (sut.yaml)
```yaml
name: "My API"
default_headers:
  X-Correlation-ID: "{{correlation_id}}"
services:
  api:
    base_url: "http://localhost:8080"
    timeout_seconds: 30
```

### Scenario (scenario.yaml)
```yaml
id: "user_checkout"
description: "User checkout flow"
flow:
  - type: http
    name: get_products
    service: api
    method: GET
    path: /api/products
    extract:
      product_id: "$.items[0].id"
  - type: assert
    name: verify_product
    expect:
      jsonpath: "$.items"
      operator: "not_empty"
```

## Code Style

- Google docstring convention
- Type hints required (mypy strict mode)
- Ruff for linting and formatting
- 88 character line length
- UTC-aware datetimes (`datetime.now(UTC)` not `utcnow()`)
