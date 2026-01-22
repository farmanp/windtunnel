"""Tests for scenario configuration loading (FEAT-003)."""

from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import ValidationError

from windtunnel.config import (
    AssertAction,
    HttpAction,
    Scenario,
    WaitAction,
    load_scenarios,
)
from windtunnel.config.loader import ConfigLoadError, load_scenario


class TestScenarioModel:
    """Test Scenario model validation."""

    def test_minimal_valid_scenario(self) -> None:
        """Minimal scenario with just id."""
        scenario = Scenario.model_validate({"id": "test-scenario"})
        assert scenario.id == "test-scenario"
        assert scenario.max_steps == 100  # default
        assert scenario.flow == []
        assert scenario.assertions == []

    def test_full_scenario(self) -> None:
        """Scenario with all fields."""
        scenario = Scenario.model_validate({
            "id": "checkout",
            "description": "Checkout flow",
            "entry": {
                "seed_data": {"user_id": "123"},
            },
            "flow": [
                {
                    "name": "create_cart",
                    "type": "http",
                    "service": "api",
                    "method": "POST",
                    "path": "/carts",
                },
            ],
            "assertions": [
                {
                    "name": "cart_created",
                    "expect": {"status_code": 201},
                },
            ],
            "max_steps": 50,
        })
        assert scenario.id == "checkout"
        assert scenario.description == "Checkout flow"
        assert scenario.max_steps == 50
        assert len(scenario.flow) == 1
        assert len(scenario.assertions) == 1

    def test_missing_id_fails(self) -> None:
        """Scenario without id fails validation."""
        with pytest.raises(ValidationError):
            Scenario.model_validate({"description": "No ID"})


class TestActionTypes:
    """Test action type discrimination."""

    def test_http_action(self) -> None:
        """HTTP action parses correctly."""
        action = HttpAction.model_validate({
            "name": "get_user",
            "type": "http",
            "service": "api",
            "method": "GET",
            "path": "/users/123",
        })
        assert action.type == "http"
        assert action.method == "GET"
        assert action.path == "/users/123"

    def test_http_action_with_extract(self) -> None:
        """HTTP action with JSONPath extraction."""
        action = HttpAction.model_validate({
            "name": "create_user",
            "type": "http",
            "service": "api",
            "method": "POST",
            "path": "/users",
            "json": {"name": "Test"},
            "extract": {"user_id": "$.id"},
        })
        assert action.extract == {"user_id": "$.id"}

    def test_wait_action(self) -> None:
        """Wait action parses correctly."""
        action = WaitAction.model_validate({
            "name": "wait_ready",
            "type": "wait",
            "service": "api",
            "path": "/status",
            "interval_seconds": 2,
            "timeout_seconds": 60,
            "expect": {"jsonpath": "$.ready", "equals": True},
        })
        assert action.type == "wait"
        assert action.interval_seconds == 2
        assert action.timeout_seconds == 60
        assert action.expect.jsonpath == "$.ready"
        assert action.expect.equals is True

    def test_assert_action(self) -> None:
        """Assert action parses correctly."""
        action = AssertAction.model_validate({
            "name": "check_status",
            "type": "assert",
            "expect": {"status_code": 200},
        })
        assert action.type == "assert"
        assert action.expect.status_code == 200

    def test_action_discriminator_in_scenario(self) -> None:
        """Actions in flow are discriminated by type."""
        scenario = Scenario.model_validate({
            "id": "test",
            "flow": [
                {
                    "name": "http_step",
                    "type": "http",
                    "service": "api",
                    "method": "GET",
                    "path": "/test",
                },
                {
                    "name": "wait_step",
                    "type": "wait",
                    "service": "api",
                    "path": "/status",
                    "expect": {"jsonpath": "$.done", "equals": True},
                },
                {
                    "name": "assert_step",
                    "type": "assert",
                    "expect": {"status_code": 200},
                },
            ],
        })
        assert isinstance(scenario.flow[0], HttpAction)
        assert isinstance(scenario.flow[1], WaitAction)
        assert isinstance(scenario.flow[2], AssertAction)


class TestLoadScenario:
    """Test single scenario loading."""

    def test_load_valid_file(self, tmp_path: Path) -> None:
        """Load a valid scenario YAML file."""
        scenario_file = tmp_path / "test.yaml"
        scenario_file.write_text(dedent("""
            id: test-scenario
            description: A test scenario
            flow:
              - name: get_data
                type: http
                service: api
                method: GET
                path: /data
        """))

        scenario = load_scenario(scenario_file)
        assert scenario.id == "test-scenario"
        assert len(scenario.flow) == 1

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Loading nonexistent file raises error."""
        with pytest.raises(ConfigLoadError, match="not found"):
            load_scenario(tmp_path / "nonexistent.yaml")

    def test_load_validation_error(self, tmp_path: Path) -> None:
        """Validation errors are reported."""
        scenario_file = tmp_path / "invalid.yaml"
        scenario_file.write_text(dedent("""
            description: Missing ID
        """))

        with pytest.raises(ConfigLoadError, match="validation failed"):
            load_scenario(scenario_file)


class TestLoadScenarios:
    """Test loading scenarios from directory."""

    def test_load_multiple_scenarios(self, tmp_path: Path) -> None:
        """Load all scenarios from directory."""
        (tmp_path / "checkout.yaml").write_text("id: checkout")
        (tmp_path / "refund.yaml").write_text("id: refund")

        scenarios = load_scenarios(tmp_path)
        assert len(scenarios) == 2
        ids = {s.id for s in scenarios}
        assert ids == {"checkout", "refund"}

    def test_load_yml_extension(self, tmp_path: Path) -> None:
        """Load scenarios with .yml extension."""
        (tmp_path / "test.yml").write_text("id: test-yml")

        scenarios = load_scenarios(tmp_path)
        assert len(scenarios) == 1
        assert scenarios[0].id == "test-yml"

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory raises error."""
        with pytest.raises(ConfigLoadError, match="No scenario files"):
            load_scenarios(tmp_path)

    def test_directory_not_found(self, tmp_path: Path) -> None:
        """Nonexistent directory raises error."""
        with pytest.raises(ConfigLoadError, match="not found"):
            load_scenarios(tmp_path / "nonexistent")

    def test_duplicate_ids(self, tmp_path: Path) -> None:
        """Duplicate scenario IDs raise error."""
        (tmp_path / "first.yaml").write_text("id: duplicate")
        (tmp_path / "second.yaml").write_text("id: duplicate")

        with pytest.raises(ConfigLoadError, match="Duplicate scenario ID"):
            load_scenarios(tmp_path)

    def test_partial_failures(self, tmp_path: Path) -> None:
        """Invalid scenarios cause overall failure."""
        (tmp_path / "valid.yaml").write_text("id: valid")
        (tmp_path / "invalid.yaml").write_text("missing_id: true")

        with pytest.raises(ConfigLoadError):
            load_scenarios(tmp_path)

    def test_load_fixture_scenarios(self) -> None:
        """Load fixture scenario files."""
        fixture_path = Path(__file__).parent / "fixtures" / "scenarios"
        if fixture_path.exists():
            scenarios = load_scenarios(fixture_path)
            assert len(scenarios) >= 2
            ids = {s.id for s in scenarios}
            assert "checkout-happy-path" in ids
            assert "refund-flow" in ids
