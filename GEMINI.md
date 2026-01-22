# Turbulence

A powerful workflow simulation and testing framework designed to stress-test and analyze complex distributed systems through realistic agent-based behavior.

## 🚀 Overview

Turbulence allows developers to define system configurations (SUT) and scenarios to simulate high-concurrency, long-running workflows. It provides deep visibility into system performance, failure modes, and recovery behaviors.

## 🛠 Project Structure

- `src/turbulence/`: Core package.
  - `cli.py`: Typer-based command-line interface.
  - `commands/`: Implementation of `run`, `report`, and `replay` commands.
  - `config/`: Configuration loaders for SUT and Scenarios.
  - `actions/`: Action execution engine (HTTP, Wait, etc.).
  - `engine/`: The core simulation runner.
  - `models/`: Data models (Pydantic).
  - `storage/`: Artifact and result persistence.
- `tests/`: Comprehensive test suite.
- `tickets/`: Project management and roadmap.

## 🚦 Getting Started

### Installation

```bash
# Recommended: create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Development Workflow

We use `pre-commit` to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run manual checks
ruff check src/
ruff format src/
mypy src/
pytest
```

## 📈 Roadmap

See [TICKET-GRAPH.md](tickets/TICKET-GRAPH.md) for the detailed dependency graph and implementation plan.

### Core Batches:
1. **Foundation**: Project scaffolding (INFRA-001) - **DONE**
2. **CLI & Config**: CLI and SUT/Scenario loading (FEAT-001, 002, 003) - **DONE**
3. **Action Runners**: HTTP, Wait, and Assertions (FEAT-004, 005, 006) - **DONE**
4. **Context Engine**: Variable management and templating (FEAT-007) - **DONE**
5. **Persistence/Reporting**: Result storage, HTML reports, and Replay (FEAT-008, 009, 010) - **DONE**
6. **Scale & Resilience**: Parallel execution, Turbulence, and Advanced Assertions (FEAT-011, 012, 013, 014) - **DONE**
7. **Web Intelligence**: Web UI, Backend API, Dashboards, and Real-time Streaming (FEAT-020, 021, 022, 023, 024, 025) - **DONE**
8. **Enterprise Readiness**: Retry policies, Env vars, Profiles (FEAT-030, 031, 032) - **DONE**
9. **Polish & CI**: Reports, CI Gating, Variation (FEAT-015, 016, 017) - **DONE**
10. **Web UI Enhancements**: Live Progress, Visualizer, Quick Launcher, Results Explorer (FEAT-026, 027, 028, 029) - **DONE**
11. **Advanced Engine**: SQLite Backend, Branching Flows, Research Spikes (FEAT-018, 019, SPIKE-001, 002, 003) - **DONE**

## 📄 License

MIT
