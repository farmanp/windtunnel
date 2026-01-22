# AI-Ready Infra Template

## 1. Objective (Required)
**What:**
Initialize the Windtunnel Python project with proper package structure, dependencies, and development tooling.

**Why:**
This establishes the foundation for all subsequent development. A well-structured project with proper tooling enables efficient development, testing, and CI/CD from day one.

## 2. Scope (Required)
**In Scope:**
- Create pyproject.toml with all core dependencies
- Set up src/windtunnel/ package structure
- Configure pytest for testing
- Set up GitHub Actions CI workflow
- Configure development tools (ruff, mypy)

**Out of Scope:**
- Actual implementation code (handled in subsequent tickets)
- Production deployment configuration
- Docker containerization

## 3. Technical Approach
**Strategy:**
Use modern Python packaging with pyproject.toml (PEP 621). Follow src-layout for better import isolation during development.

**Files to Create:**
- `pyproject.toml` - Project metadata and dependencies
- `src/windtunnel/__init__.py` - Package root
- `src/windtunnel/py.typed` - PEP 561 marker
- `tests/__init__.py` - Test package
- `tests/conftest.py` - Pytest fixtures
- `.github/workflows/ci.yml` - CI workflow

**Dependencies:**
Core:
- typer[all] >= 0.9.0 - CLI framework
- pydantic >= 2.0 - Data validation
- httpx >= 0.25.0 - Async HTTP client
- jsonpath-ng >= 1.6.0 - JSONPath extraction
- jinja2 >= 3.1.0 - Template engine
- rich >= 13.0 - Terminal formatting

Dev:
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- pytest-cov >= 4.1.0
- ruff >= 0.1.0
- mypy >= 1.5.0

## 4. Acceptance Criteria (Required)
- [ ] `pip install -e .` succeeds from project root
- [ ] `python -c "import windtunnel"` works
- [ ] `pytest` runs (even with no tests yet)
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes
- [ ] GitHub Actions workflow runs on push/PR
- [ ] No breaking changes to existing functionality (N/A - greenfield)

## 5. Rollback Plan
Delete the repository and start fresh (greenfield project).

## 6. Planned Git Commit Message(s)
- chore(infra): initialize python project with dependencies and tooling

## 7. Verification
- [ ] Acceptance criteria pass
- [ ] CI workflow succeeds
- [ ] All dev dependencies install correctly
- [ ] Package structure follows Python best practices
