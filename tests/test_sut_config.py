"""Tests for SUT configuration loading (FEAT-002)."""

from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import ValidationError

from windtunnel.config import SUTConfig, load_sut
from windtunnel.config.loader import ConfigLoadError


class TestSUTConfig:
    """Test SUTConfig model validation."""

    def test_valid_config(self) -> None:
        """Valid config with all required fields."""
        config = SUTConfig.model_validate({
            "name": "test-system",
            "services": {
                "api": {"base_url": "https://api.example.com"},
            },
        })
        assert config.name == "test-system"
        assert "api" in config.services
        assert str(config.services["api"].base_url) == "https://api.example.com/"

    def test_multiple_services(self) -> None:
        """Config with multiple services."""
        config = SUTConfig.model_validate({
            "name": "multi-service",
            "services": {
                "api": {"base_url": "https://api.example.com"},
                "payments": {"base_url": "https://payments.example.com"},
                "notifications": {"base_url": "https://notifications.example.com"},
            },
        })
        assert len(config.services) == 3
        assert "api" in config.services
        assert "payments" in config.services
        assert "notifications" in config.services

    def test_default_headers(self) -> None:
        """Config with default headers including templates."""
        config = SUTConfig.model_validate({
            "name": "test",
            "default_headers": {
                "X-Run-ID": "{{run_id}}",
                "X-Correlation-ID": "{{correlation_id}}",
                "Content-Type": "application/json",
            },
            "services": {
                "api": {"base_url": "https://api.example.com"},
            },
        })
        assert config.default_headers["X-Run-ID"] == "{{run_id}}"
        assert config.default_headers["Content-Type"] == "application/json"

    def test_service_specific_headers(self) -> None:
        """Service with its own headers."""
        config = SUTConfig.model_validate({
            "name": "test",
            "default_headers": {"Content-Type": "application/json"},
            "services": {
                "payments": {
                    "base_url": "https://payments.example.com",
                    "headers": {"X-API-Key": "secret"},
                },
            },
        })
        merged = config.get_headers_for_service("payments")
        assert merged["Content-Type"] == "application/json"
        assert merged["X-API-Key"] == "secret"

    def test_missing_name_fails(self) -> None:
        """Config without name fails validation."""
        with pytest.raises(ValidationError):
            SUTConfig.model_validate({
                "services": {"api": {"base_url": "https://api.example.com"}},
            })

    def test_missing_services_fails(self) -> None:
        """Config without services fails validation."""
        with pytest.raises(ValidationError):
            SUTConfig.model_validate({"name": "test"})

    def test_service_missing_base_url_fails(self) -> None:
        """Service without base_url fails validation."""
        with pytest.raises(ValidationError):
            SUTConfig.model_validate({
                "name": "test",
                "services": {"api": {}},
            })

    def test_get_service(self) -> None:
        """get_service returns correct service."""
        config = SUTConfig.model_validate({
            "name": "test",
            "services": {
                "api": {"base_url": "https://api.example.com"},
            },
        })
        service = config.get_service("api")
        assert str(service.base_url) == "https://api.example.com/"

    def test_get_service_not_found(self) -> None:
        """get_service raises KeyError for unknown service."""
        config = SUTConfig.model_validate({
            "name": "test",
            "services": {
                "api": {"base_url": "https://api.example.com"},
            },
        })
        with pytest.raises(KeyError, match="nonexistent"):
            config.get_service("nonexistent")


class TestLoadSUT:
    """Test SUT config loading from YAML files."""

    def test_load_valid_file(self, tmp_path: Path) -> None:
        """Load a valid SUT YAML file."""
        sut_file = tmp_path / "sut.yaml"
        sut_file.write_text(dedent("""
            name: test-system
            services:
              api:
                base_url: https://api.example.com
        """))

        config = load_sut(sut_file)
        assert config.name == "test-system"

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Loading nonexistent file raises error."""
        with pytest.raises(ConfigLoadError, match="not found"):
            load_sut(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Loading invalid YAML raises error."""
        sut_file = tmp_path / "sut.yaml"
        sut_file.write_text("invalid: yaml: syntax: [")

        with pytest.raises(ConfigLoadError, match="Invalid YAML"):
            load_sut(sut_file)

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Loading empty file raises error."""
        sut_file = tmp_path / "sut.yaml"
        sut_file.write_text("")

        with pytest.raises(ConfigLoadError, match="empty"):
            load_sut(sut_file)

    def test_load_validation_error(self, tmp_path: Path) -> None:
        """Validation errors are reported clearly."""
        sut_file = tmp_path / "sut.yaml"
        sut_file.write_text(dedent("""
            name: test
            services:
              api: {}
        """))

        with pytest.raises(ConfigLoadError, match="validation failed"):
            load_sut(sut_file)

    def test_load_fixture_file(self) -> None:
        """Load the fixture sut.yaml file."""
        fixture_path = Path(__file__).parent / "fixtures" / "sut.yaml"
        if fixture_path.exists():
            config = load_sut(fixture_path)
            assert config.name == "ecommerce-checkout"
            assert "api" in config.services
            assert "payments" in config.services
            assert "notifications" in config.services
