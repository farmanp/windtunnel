"""Routes for configuration listing and run triggering."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from turbulence.commands.run import (
    _run_instances,
    generate_run_id,
    load_scenarios_from_paths,
)
from turbulence.config.loader import ConfigLoadError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["configs"])


class SutConfigSummary(BaseModel):
    name: str
    path: str
    file_name: str


class ScenarioSummary(BaseModel):
    id: str
    description: str
    path: str
    file_name: str


class SutConfigListResponse(BaseModel):
    configs: list[SutConfigSummary]


class ScenarioListResponse(BaseModel):
    scenarios: list[ScenarioSummary]


class ScenarioContentResponse(BaseModel):
    path: str
    content: str


class RunTriggerRequest(BaseModel):
    sut_path: str = Field(..., min_length=1)
    scenario_paths: list[str] = Field(default_factory=list)
    instances: int = Field(default=10, ge=1, le=1000)
    parallelism: int = Field(default=5, ge=1, le=100)
    profile: str | None = None


class RunTriggerResponse(BaseModel):
    run_id: str


def _list_yaml_files(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    files = list(base_dir.rglob("*.yaml")) + list(base_dir.rglob("*.yml"))
    return sorted([path for path in files if path.is_file()], key=lambda path: path.as_posix())


def _read_yaml_metadata(path: Path) -> dict[str, object]:
    try:
        with path.open() as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError:
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _resolve_relative_path(base_dir: Path, relative_path: str) -> Path:
    rel_path = Path(relative_path)
    if rel_path.is_absolute():
        raise HTTPException(status_code=400, detail="Path must be relative.")
    resolved = (base_dir / rel_path).resolve()
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Path is outside base directory.") from exc
    return resolved


@router.get("/configs/sut", response_model=SutConfigListResponse)
def list_sut_configs(request: Request) -> SutConfigListResponse:
    """List available SUT configuration files."""
    sut_dir: Path = request.app.state.sut_dir
    configs: list[SutConfigSummary] = []
    for path in _list_yaml_files(sut_dir):
        data = _read_yaml_metadata(path)
        name = str(data.get("name") or path.stem)
        configs.append(
            SutConfigSummary(
                name=name,
                path=path.relative_to(sut_dir).as_posix(),
                file_name=path.name,
            )
        )
    return SutConfigListResponse(configs=configs)


@router.get("/configs/scenarios", response_model=ScenarioListResponse)
def list_scenarios(request: Request) -> ScenarioListResponse:
    """List available scenario files."""
    scenarios_dir: Path = request.app.state.scenarios_dir
    scenarios: list[ScenarioSummary] = []
    for path in _list_yaml_files(scenarios_dir):
        data = _read_yaml_metadata(path)
        scenario_id = str(data.get("id") or path.stem)
        description = str(data.get("description") or "")
        scenarios.append(
            ScenarioSummary(
                id=scenario_id,
                description=description,
                path=path.relative_to(scenarios_dir).as_posix(),
                file_name=path.name,
            )
        )
    return ScenarioListResponse(scenarios=scenarios)


@router.get("/configs/scenarios/content", response_model=ScenarioContentResponse)
def get_scenario_content(
    request: Request, path: str = Query(..., min_length=1)
) -> ScenarioContentResponse:
    """Fetch the raw content of a scenario file."""
    scenarios_dir: Path = request.app.state.scenarios_dir
    scenario_path = _resolve_relative_path(scenarios_dir, path)
    if not scenario_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found.")
    if not scenario_path.is_file():
        raise HTTPException(status_code=400, detail="Scenario path is not a file.")
    content = scenario_path.read_text(encoding="utf-8")
    return ScenarioContentResponse(path=path, content=content)


def _handle_run_task(task: asyncio.Task[int], run_id: str) -> None:
    try:
        exit_code = task.result()
        if exit_code != 0:
            logger.warning("Run %s completed with exit code %s", run_id, exit_code)
    except Exception:
        logger.exception("Run %s failed", run_id)


@router.post("/runs/trigger", response_model=RunTriggerResponse)
async def trigger_run(request: Request, trigger: RunTriggerRequest) -> RunTriggerResponse:
    """Trigger a new simulation run."""
    sut_dir: Path = request.app.state.sut_dir
    scenarios_dir: Path = request.app.state.scenarios_dir
    runs_dir: Path = request.app.state.runs_dir

    if not trigger.scenario_paths:
        raise HTTPException(status_code=400, detail="At least one scenario is required.")

    sut_path = _resolve_relative_path(sut_dir, trigger.sut_path)
    if not sut_path.exists():
        raise HTTPException(status_code=404, detail="SUT config not found.")
    if not sut_path.is_file():
        raise HTTPException(status_code=400, detail="SUT config path is not a file.")

    scenario_paths: list[Path] = []
    for rel_path in trigger.scenario_paths:
        scenario_path = _resolve_relative_path(scenarios_dir, rel_path)
        if not scenario_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scenario '{rel_path}' not found.",
            )
        if not scenario_path.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Scenario '{rel_path}' is not a file.",
            )
        scenario_paths.append(scenario_path)

    try:
        scenario_list = load_scenarios_from_paths(scenario_paths)
    except (ConfigLoadError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run_id = generate_run_id()
    scenarios_label = f"{len(scenario_list)} selected scenario(s)"

    task = asyncio.create_task(
        _run_instances(
            sut=sut_path,
            scenarios_dir=None,
            scenario_list=scenario_list,
            scenarios_label=scenarios_label,
            instances=trigger.instances,
            parallelism=trigger.parallelism,
            seed=None,
            profile=trigger.profile,
            output_dir=runs_dir,
            fail_on=None,
            storage="jsonl",
            run_id=run_id,
        )
    )
    task.add_done_callback(lambda done_task: _handle_run_task(done_task, run_id))

    return RunTriggerResponse(run_id=run_id)
