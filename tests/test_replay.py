"""Tests for replay command and engine."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from windtunnel.config.scenario import HttpAction, Scenario
from windtunnel.config.sut import Service, SUTConfig
from windtunnel.engine.replay import (
    InstanceData,
    InstanceNotFoundError,
    ReplayEngine,
    ReplayResult,
    ScenarioNotFoundError,
    StepResult,
)
from windtunnel.models.observation import Observation


@pytest.fixture
def sut_config() -> SUTConfig:
    """Create a sample SUT configuration."""
    return SUTConfig(
        name="test-system",
        default_headers={"X-Default-Header": "default-value"},
        services={
            "api": Service(
                base_url="https://api.example.com",  # type: ignore[arg-type]
                headers={"X-Service-Header": "service-value"},
                timeout_seconds=10.0,
            ),
        },
    )


@pytest.fixture
def sample_instance_data() -> dict[str, Any]:
    """Create sample instance data for testing."""
    return {
        "instance_id": "inst_test123",
        "run_id": "run_001",
        "correlation_id": "corr_abc123",
        "scenario_id": "test_scenario",
        "seed": 42,
        "entry": {"seed_data": {"user_id": "user_001"}},
        "results": [
            {
                "ok": True,
                "status_code": 200,
                "latency_ms": 150.5,
                "action_name": "get-user",
            },
            {
                "ok": True,
                "status_code": 201,
                "latency_ms": 200.0,
                "action_name": "create-order",
            },
        ],
    }


@pytest.fixture
def temp_runs_dir(tmp_path: Path, sample_instance_data: dict[str, Any]) -> Path:
    """Create a temporary runs directory with test data."""
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "run_001"
    run_dir.mkdir(parents=True)

    # Write instances.jsonl file
    instances_file = run_dir / "instances.jsonl"
    with instances_file.open("w") as f:
        f.write(json.dumps(sample_instance_data) + "\n")
        # Add another instance for testing
        other_instance = sample_instance_data.copy()
        other_instance["instance_id"] = "inst_other456"
        other_instance["correlation_id"] = "corr_other789"
        f.write(json.dumps(other_instance) + "\n")

    return runs_dir


@pytest.fixture
def temp_scenarios_dir(tmp_path: Path) -> Path:
    """Create a temporary scenarios directory with test scenario."""
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir(parents=True)

    scenario_data = {
        "id": "test_scenario",
        "description": "Test scenario for replay",
        "entry": {"seed_data": {}},
        "flow": [
            {
                "name": "get-user",
                "type": "http",
                "service": "api",
                "method": "GET",
                "path": "/users/{{entry.seed_data.user_id}}",
            },
            {
                "name": "create-order",
                "type": "http",
                "service": "api",
                "method": "POST",
                "path": "/orders",
                "json": {"user_id": "{{entry.seed_data.user_id}}"},
            },
        ],
        "assertions": [],
        "stop_when": {"any_action_fails": False},
    }

    import yaml

    scenario_file = scenarios_dir / "test_scenario.yaml"
    with scenario_file.open("w") as f:
        yaml.dump(scenario_data, f)

    return scenarios_dir


class TestInstanceData:
    """Tests for InstanceData dataclass."""

    def test_from_dict(self, sample_instance_data: dict[str, Any]) -> None:
        """Test creating InstanceData from a dictionary."""
        instance = InstanceData.from_dict(sample_instance_data)

        assert instance.instance_id == "inst_test123"
        assert instance.run_id == "run_001"
        assert instance.correlation_id == "corr_abc123"
        assert instance.scenario_id == "test_scenario"
        assert instance.seed == 42
        assert instance.entry == {"seed_data": {"user_id": "user_001"}}
        assert len(instance.original_results) == 2

    def test_from_dict_with_missing_optional_fields(self) -> None:
        """Test creating InstanceData with minimal data."""
        minimal_data = {
            "instance_id": "inst_minimal",
            "run_id": "run_min",
            "correlation_id": "corr_min",
            "scenario_id": "scenario_min",
        }
        instance = InstanceData.from_dict(minimal_data)

        assert instance.instance_id == "inst_minimal"
        assert instance.seed == 0
        assert instance.entry == {}
        assert instance.original_results == []


class TestReplayEngine:
    """Tests for ReplayEngine class."""

    def test_load_instance_success(
        self, temp_runs_dir: Path, sample_instance_data: dict[str, Any]
    ) -> None:
        """Test loading an instance successfully."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)
        instance = engine.load_instance("run_001", "inst_test123")

        assert instance.instance_id == "inst_test123"
        assert instance.correlation_id == "corr_abc123"
        assert instance.scenario_id == "test_scenario"

    def test_load_instance_not_found(self, temp_runs_dir: Path) -> None:
        """Test loading a non-existent instance raises error."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)

        with pytest.raises(InstanceNotFoundError) as exc_info:
            engine.load_instance("run_001", "inst_nonexistent")

        assert "inst_nonexistent" in str(exc_info.value)
        assert "run_001" in str(exc_info.value)

    def test_load_instance_run_not_found(self, temp_runs_dir: Path) -> None:
        """Test loading from non-existent run raises error."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)

        with pytest.raises(InstanceNotFoundError) as exc_info:
            engine.load_instance("run_nonexistent", "inst_test123")

        assert "run_nonexistent" in str(exc_info.value)

    def test_load_scenario_success(
        self, temp_runs_dir: Path, temp_scenarios_dir: Path
    ) -> None:
        """Test loading a scenario successfully."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
        )
        scenario = engine.load_scenario("test_scenario")

        assert scenario.id == "test_scenario"
        assert len(scenario.flow) == 2

    def test_load_scenario_not_found(
        self, temp_runs_dir: Path, temp_scenarios_dir: Path
    ) -> None:
        """Test loading non-existent scenario raises error."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
        )

        with pytest.raises(ScenarioNotFoundError) as exc_info:
            engine.load_scenario("nonexistent_scenario")

        assert "nonexistent_scenario" in str(exc_info.value)

    def test_load_scenario_no_scenarios_dir(self, temp_runs_dir: Path) -> None:
        """Test loading scenario without scenarios_dir raises error."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)

        with pytest.raises(ScenarioNotFoundError):
            engine.load_scenario("test_scenario")

    def test_create_context_from_instance(
        self, temp_runs_dir: Path, sample_instance_data: dict[str, Any]
    ) -> None:
        """Test creating WorkflowContext from instance data."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)
        instance = InstanceData.from_dict(sample_instance_data)
        ctx = engine.create_context_from_instance(instance)

        assert ctx.run_id == "run_001"
        assert ctx.instance_id == "inst_test123"
        assert ctx.correlation_id == "corr_abc123"
        assert ctx.entry == {"seed_data": {"user_id": "user_001"}}

    def test_compare_observations_no_difference(self) -> None:
        """Test comparing observations with no difference."""
        engine = ReplayEngine(runs_dir=Path("."))
        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=100.0,
        )
        original = {"ok": True, "status_code": 200}

        has_diff, details = engine._compare_observations(observation, original)

        assert has_diff is False
        assert details is None

    def test_compare_observations_with_status_difference(self) -> None:
        """Test comparing observations with status code difference."""
        engine = ReplayEngine(runs_dir=Path("."))
        observation = Observation(
            ok=False,
            status_code=500,
            latency_ms=100.0,
        )
        original = {"ok": True, "status_code": 200}

        has_diff, details = engine._compare_observations(observation, original)

        assert has_diff is True
        assert details is not None
        assert "status_code" in details
        assert "200" in details
        assert "500" in details

    def test_compare_observations_no_original(self) -> None:
        """Test comparing when original observation is None."""
        engine = ReplayEngine(runs_dir=Path("."))
        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=100.0,
        )

        has_diff, details = engine._compare_observations(observation, None)

        assert has_diff is False
        assert details is None

    @pytest.mark.asyncio
    async def test_execute_step_http_action(
        self, temp_runs_dir: Path, sut_config: SUTConfig
    ) -> None:
        """Test executing an HTTP action step."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            sut_config=sut_config,
        )
        action = HttpAction(
            name="test-action",
            service="api",
            method="GET",
            path="/users/123",
        )
        context = {"user_id": 123}

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "name": "Test User"},
            headers={"Content-Type": "application/json"},
        )

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, updated_context = await engine.execute_step(action, context)

        assert observation.ok is True
        assert observation.status_code == 200
        assert observation.action_name == "test-action"

    @pytest.mark.asyncio
    async def test_replay_full_execution(
        self,
        temp_runs_dir: Path,
        temp_scenarios_dir: Path,
        sut_config: SUTConfig,
    ) -> None:
        """Test full replay execution."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
            sut_config=sut_config,
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "status": "ok"},
            headers={"Content-Type": "application/json"},
        )

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await engine.replay("run_001", "inst_test123")

        assert result.instance_id == "inst_test123"
        assert result.correlation_id == "corr_abc123"
        assert result.scenario_id == "test_scenario"
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_replay_instance_not_found(self, temp_runs_dir: Path) -> None:
        """Test replay with non-existent instance."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)
        result = await engine.replay("run_001", "inst_nonexistent")

        assert result.success is False
        assert result.error is not None
        assert "inst_nonexistent" in result.error

    @pytest.mark.asyncio
    async def test_replay_preserves_correlation_id(
        self,
        temp_runs_dir: Path,
        temp_scenarios_dir: Path,
        sut_config: SUTConfig,
    ) -> None:
        """Test that replay preserves the original correlation ID."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
            sut_config=sut_config,
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await engine.replay("run_001", "inst_test123")

        # Verify correlation ID is in headers
        assert sut_config.default_headers.get("X-Correlation-ID") == "corr_abc123"
        assert result.correlation_id == "corr_abc123"


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_creation(self) -> None:
        """Test creating a StepResult."""
        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=150.5,
            action_name="test-action",
        )
        step = StepResult(
            step_number=1,
            action_name="test-action",
            action_type="http",
            observation=observation,
            has_difference=False,
        )

        assert step.step_number == 1
        assert step.action_name == "test-action"
        assert step.action_type == "http"
        assert step.observation.ok is True

    def test_step_result_with_difference(self) -> None:
        """Test StepResult with a difference from original."""
        observation = Observation(
            ok=False,
            status_code=500,
            latency_ms=150.5,
            action_name="test-action",
        )
        step = StepResult(
            step_number=1,
            action_name="test-action",
            action_type="http",
            observation=observation,
            original_observation={"ok": True, "status_code": 200},
            has_difference=True,
            difference_details="status_code: original=200, replay=500",
        )

        assert step.has_difference is True
        assert "status_code" in (step.difference_details or "")


class TestReplayResult:
    """Tests for ReplayResult dataclass."""

    def test_replay_result_success(self) -> None:
        """Test creating a successful ReplayResult."""
        result = ReplayResult(
            instance_id="inst_test",
            correlation_id="corr_test",
            scenario_id="scenario_test",
            success=True,
            steps=[],
        )

        assert result.success is True
        assert result.error is None

    def test_replay_result_failure(self) -> None:
        """Test creating a failed ReplayResult."""
        result = ReplayResult(
            instance_id="inst_test",
            correlation_id="corr_test",
            scenario_id="scenario_test",
            success=False,
            error="Instance not found",
        )

        assert result.success is False
        assert result.error == "Instance not found"


class TestReplayCommand:
    """Tests for the replay CLI command."""

    def test_replay_run_not_found(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test replay with non-existent run."""
        from windtunnel.cli import app

        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()

        result = cli_runner.invoke(
            app,
            [
                "replay",
                "--run-id",
                "nonexistent_run",
                "--instance-id",
                "inst_001",
                "--runs-dir",
                str(runs_dir),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_replay_instance_not_found(
        self, cli_runner: CliRunner, temp_runs_dir: Path
    ) -> None:
        """Test replay with non-existent instance."""
        from windtunnel.cli import app

        result = cli_runner.invoke(
            app,
            [
                "replay",
                "--run-id",
                "run_001",
                "--instance-id",
                "nonexistent_instance",
                "--runs-dir",
                str(temp_runs_dir),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_replay_without_sut_shows_instance_data(
        self, cli_runner: CliRunner, temp_runs_dir: Path
    ) -> None:
        """Test replay without SUT config shows instance data only."""
        from windtunnel.cli import app

        result = cli_runner.invoke(
            app,
            [
                "replay",
                "--run-id",
                "run_001",
                "--instance-id",
                "inst_test123",
                "--runs-dir",
                str(temp_runs_dir),
            ],
        )

        assert result.exit_code == 0
        assert "inst_test123" in result.output
        assert "corr_abc123" in result.output
        assert "No SUT config" in result.output or "Warning" in result.output


class TestReplayEdgeCases:
    """Tests for edge cases in replay functionality."""

    def test_empty_instances_file(self, tmp_path: Path) -> None:
        """Test loading from empty instances file."""
        runs_dir = tmp_path / "runs"
        run_dir = runs_dir / "run_empty"
        run_dir.mkdir(parents=True)

        instances_file = run_dir / "instances.jsonl"
        instances_file.touch()

        engine = ReplayEngine(runs_dir=runs_dir)

        with pytest.raises(InstanceNotFoundError):
            engine.load_instance("run_empty", "any_instance")

    def test_malformed_jsonl_line(self, tmp_path: Path) -> None:
        """Test handling malformed JSON lines in instances file."""
        runs_dir = tmp_path / "runs"
        run_dir = runs_dir / "run_bad"
        run_dir.mkdir(parents=True)

        instances_file = run_dir / "instances.jsonl"
        with instances_file.open("w") as f:
            f.write("not valid json\n")
            f.write(
                json.dumps(
                    {
                        "instance_id": "inst_valid",
                        "run_id": "run_bad",
                        "correlation_id": "corr_valid",
                        "scenario_id": "test",
                    }
                )
                + "\n"
            )

        engine = ReplayEngine(runs_dir=runs_dir)
        instance = engine.load_instance("run_bad", "inst_valid")

        assert instance.instance_id == "inst_valid"

    def test_multiple_instances_in_file(
        self, temp_runs_dir: Path, sample_instance_data: dict[str, Any]
    ) -> None:
        """Test loading correct instance from file with multiple instances."""
        engine = ReplayEngine(runs_dir=temp_runs_dir)

        # Load the second instance
        instance = engine.load_instance("run_001", "inst_other456")
        assert instance.instance_id == "inst_other456"
        assert instance.correlation_id == "corr_other789"

        # Load the first instance
        instance = engine.load_instance("run_001", "inst_test123")
        assert instance.instance_id == "inst_test123"
        assert instance.correlation_id == "corr_abc123"

    @pytest.mark.asyncio
    async def test_replay_with_action_failure(
        self,
        temp_runs_dir: Path,
        temp_scenarios_dir: Path,
        sut_config: SUTConfig,
    ) -> None:
        """Test replay when an action fails."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
            sut_config=sut_config,
        )

        mock_response = httpx.Response(
            status_code=500,
            json={"error": "Internal Server Error"},
            headers={"Content-Type": "application/json"},
        )
        mock_response._request = httpx.Request("GET", "https://api.example.com/users")

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await engine.replay("run_001", "inst_test123")

        assert result.success is False
        # Should still have step results
        assert len(result.steps) > 0
        assert result.steps[0].observation.ok is False

    @pytest.mark.asyncio
    async def test_replay_detects_difference_from_original(
        self,
        temp_runs_dir: Path,
        temp_scenarios_dir: Path,
        sut_config: SUTConfig,
    ) -> None:
        """Test that replay detects differences from original execution."""
        engine = ReplayEngine(
            runs_dir=temp_runs_dir,
            scenarios_dir=temp_scenarios_dir,
            sut_config=sut_config,
        )

        # Original had status 200, but replay returns 500
        mock_response = httpx.Response(
            status_code=500,
            json={"error": "Server Error"},
            headers={"Content-Type": "application/json"},
        )
        mock_response._request = httpx.Request("GET", "https://api.example.com/users")

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await engine.replay("run_001", "inst_test123")

        # First step should show difference (original was 200, replay is 500)
        assert result.steps[0].has_difference is True
        assert "status_code" in (result.steps[0].difference_details or "")
