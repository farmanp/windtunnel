# Repository Guidelines

## Project Structure & Module Organization

- `src/windtunnel/` contains the library and CLI implementation. Key modules include `actions/`, `commands/`, `config/`, `engine/`, `models/`, `report/`, and `storage/`.
- `tests/` contains pytest suites and fixtures. Scenario samples live under `tests/fixtures/scenarios/`.
- `tickets/` holds planning and design notes for features and infra work.
- Module-level `CLAUDE.md` files document local conventions; skim the nearest one before making changes in that area.

## Build, Test, and Development Commands

- `pip install -e ".[dev]"` installs the package in editable mode with dev tooling.
- `windtunnel --help` verifies CLI wiring and lists available commands.
- `pytest tests/` runs the test suite.
- `ruff check src/ tests/` runs linting.
- `mypy src/` runs strict type checking.

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indentation, line length 88.
- Prefer double quotes (Ruff formatter configuration).
- Type annotations are expected everywhere (`mypy` is strict and disallows untyped defs).
- Use snake_case for functions/modules, PascalCase for classes, and descriptive CLI command names.

## Testing Guidelines

- Framework: `pytest` with `pytest-asyncio` enabled (`asyncio_mode=auto`).
- Test files use `test_*.py` naming; fixtures live in `tests/fixtures/`.
- Add coverage for new actions, engine behavior, and CLI commands; include both success and error paths.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits patterns seen in history, e.g. `feat: ...` or `feat(engine): ...`.
- PRs should include: a short summary, testing notes (commands run), and any relevant `tickets/` references.
- Include screenshots for report/HTML changes (see `src/windtunnel/report/templates/`).

## Configuration & Security Notes

- Scenario/SUT configs are YAML-based (see `tests/fixtures/` for examples).
- The lint rules include security checks (`ruff`’s `S` rules); resolve warnings before merging.
