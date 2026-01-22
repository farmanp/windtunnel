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
│   ├── scenario.py          # Scenario/flow definitions
│   └── loader.py            # YAML loading and validation
├── actions/                  # Action runners (implement BaseAction)
│   ├── base.py              # BaseAction abstract class
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
├── user/                    # User guides
│   └── guides/              # Tutorial guides (e.g., ecommerce-testing.md)

tickets/                      # Feature tickets and roadmap
├── TICKET-GRAPH.md          # Dependency graph and batch planning
├── FEAT-*.md                # Feature specifications
└── SPIKE-*.md               # Research spikes

use-cases/                    # Use case validation
├── UC-*.md                  # Use case documentation
├── scenarios/               # Working scenario examples
└── sut/                     # SUT config examples
```

### Key Patterns

**Action Runner Interface**: All actions implement `BaseAction.execute(context) -> Observation`

**Observation Model**: Unified result format with `ok`, `status_code`, `latency_ms`, `headers`, `body`, `errors`

**Context Flow**: SUT config + scenario → template engine → action runners → observations → artifact storage

**Parallel Execution**: `asyncio.Semaphore` controls concurrency, graceful cancellation preserves partial results

**Safe Expressions**: AST validation whitelist prevents code injection while enabling complex assertions

**Assertions**: Separate `assert` actions in flow (not inline with HTTP actions)

## Technology Stack

- **Python 3.10+**: Core framework (tested on 3.11, 3.12, 3.13, 3.14)
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
# Run workflow simulation
turbulence run --sut sut.yaml --scenarios scenarios/ -n 100 -p 10

# Generate HTML report
turbulence report --run-id <run_id>

# Replay specific instance for debugging
turbulence replay --run-id <run_id> --instance-id <instance_id>

# Start web dashboard
turbulence serve --port 8000
```

**CLI Notes:**
- `--scenarios` takes a **directory** path, not a single file
- `-n` = number of instances (default: 100)
- `-p` = parallelism/concurrency (default: 10)

### Docs Site

```bash
npm run docs:start        # Start dev server at localhost:3000
npm run docs:build        # Build static site
```

## Project Status

**Completed (Batches 0-5, 8, 10, partial 6):**
- CLI scaffold with all commands
- SUT and scenario configuration
- HTTP, Wait, Assert action runners
- Context templating engine
- JSONL artifact storage
- HTML report generation (Enhanced with aggregations)
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
- CI gating with thresholds
- Live progress dashboard
- Scenario visualizer (YAML-to-Flowchart)
- Quick Run Launcher (UI-to-Engine orchestration)
- Results Explorer (Filtering, Comparison, Export)
- Python DSL Research (Design Spike)

**Upcoming:**
- Batch 6: Variation engine (FEAT-017)
- Batch 7: Advanced Engine (Spikes)

See `tickets/TICKET-GRAPH.md` for full roadmap with 32 feature tickets across 10 batches.

## Configuration Examples

### SUT Config (sut.yaml)
```yaml
name: "My API"
default_headers:
  Accept: application/json
  X-Correlation-ID: "{{correlation_id}}"
services:
  api:
    base_url: "http://localhost:8080"
    timeout_seconds: 30
```

**SUT Config Fields:**
- `name` (required): Name of the system under test
- `default_headers`: Headers applied to all requests (supports templates)
- `services` (required): Map of service names to configurations
  - `base_url` (required): Base URL for the service
  - `timeout_seconds`: Request timeout (default: 30)
  - `headers`: Service-specific headers (override defaults)

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
    name: verify_products
    expect:
      status_code: 200

  - type: http
    name: add_to_cart
    service: api
    method: POST
    path: /api/cart
    body:
      product_id: "{{product_id}}"
    extract:
      cart_id: "$.cart_id"

  - type: assert
    name: verify_cart_created
    expect:
      jsonpath: "$.cart_id"
      expression: "value is not None"

assertions:
  - name: final_check
    expect:
      status_code: 200

stop_when:
  any_action_fails: true
```

**Action Types:**
- `http`: Make HTTP request, extract values from response
- `wait`: Poll endpoint until condition met
- `assert`: Validate values with expectations

**Expectation Fields:**
- `status_code`: Expected HTTP status
- `jsonpath`: JSONPath to extract value
- `equals`: Exact match
- `contains`: Substring/member check
- `expression`: Python expression (e.g., `value > 0`)
- `schema`: JSON Schema validation

## Use Cases

The `use-cases/` directory contains validated patterns:

- **UC-001: E-commerce Checkout** - Sequential HTTP flow with extraction
  - Scenarios: `use-cases/scenarios/httpbin-test/`
  - SUT configs: `use-cases/sut/httpbin.yaml`
  - Run: `turbulence run --sut use-cases/sut/httpbin.yaml --scenarios use-cases/scenarios/httpbin-test/ -n 10`

## Code Style

- Google docstring convention
- Type hints required (mypy strict mode)
- Ruff for linting and formatting
- 88 character line length
- UTC-aware datetimes (`datetime.now(UTC)` not `utcnow()`)
- Pydantic models use `extra="forbid"` to catch typos

## Common Patterns

### Extracting and Using Values
```yaml
- type: http
  name: login
  path: /auth/login
  extract:
    token: "$.access_token"

- type: http
  name: get_profile
  path: /api/profile
  headers:
    Authorization: "Bearer {{token}}"
```

### Polling for Async Completion
```yaml
- type: wait
  name: wait_for_job
  service: api
  path: "/jobs/{{job_id}}"
  interval_seconds: 1
  timeout_seconds: 30
  expect:
    jsonpath: "$.status"
    equals: "completed"
```

### Schema Validation
```yaml
assertions:
  - name: validate_response
    expect:
      schema:
        type: object
        required: [id, status, items]
        properties:
          id: { type: string }
          status: { type: string, enum: [pending, confirmed] }
          items: { type: array, minItems: 1 }
```

## Troubleshooting

**"Service not found" error**: Check that scenario `service` field matches a key in SUT config's `services` section.

**Extraction returns null**: Use replay to see actual response, verify JSONPath against it.

**"Extra inputs not permitted"**: SUT/scenario has an unknown field. Check spelling and refer to config models in `src/turbulence/config/`.

**Tests fail in CI but pass locally**: Check for ANSI escape codes in output assertions, timezone issues, or path differences.
