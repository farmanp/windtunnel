"""Tests for HTTP action runner."""

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from windtunnel.actions.http import HttpActionRunner
from windtunnel.config.scenario import HttpAction
from windtunnel.config.sut import Service, SUTConfig
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
def mock_client() -> httpx.AsyncClient:
    """Create a mock httpx client."""
    return httpx.AsyncClient()


class TestHttpActionRunner:
    """Tests for HttpActionRunner class."""

    @pytest.mark.asyncio
    async def test_execute_get_request(self, sut_config: SUTConfig) -> None:
        """Test executing a GET request."""
        action = HttpAction(
            name="get-user",
            service="api",
            method="GET",
            path="/users/123",
        )

        # Create mock response
        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "name": "Test User"},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.status_code == 200
        assert observation.body == {"id": 123, "name": "Test User"}
        assert observation.action_name == "get-user"
        assert observation.latency_ms >= 0
        assert observation.errors == []

    @pytest.mark.asyncio
    async def test_execute_post_with_json_body(self, sut_config: SUTConfig) -> None:
        """Test executing a POST request with JSON body."""
        action = HttpAction(
            name="create-user",
            service="api",
            method="POST",
            path="/users",
            body={"name": "test"},  # Using body instead of json
        )

        mock_response = httpx.Response(
            status_code=201,
            json={"id": 456, "name": "test"},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.status_code == 201
        # Verify json was passed to request
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs.get("json") == {"name": "test"}
        assert call_kwargs.get("method") == "POST"

    @pytest.mark.asyncio
    async def test_extract_values_with_jsonpath(self, sut_config: SUTConfig) -> None:
        """Test extracting values from response using JSONPath."""
        action = HttpAction(
            name="get-user-with-extract",
            service="api",
            method="GET",
            path="/users/123",
            extract={"user_id": "$.id", "email": "$.email"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "email": "test@example.com", "name": "Test"},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is True
        assert context["user_id"] == 123
        assert context["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_extract_nested_values(self, sut_config: SUTConfig) -> None:
        """Test extracting nested values using JSONPath."""
        action = HttpAction(
            name="get-nested",
            service="api",
            method="GET",
            path="/users/123",
            extract={"city": "$.address.city", "first_tag": "$.tags[0]"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 123,
                "address": {"city": "San Francisco", "zip": "94105"},
                "tags": ["developer", "admin"],
            },
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is True
        assert context["city"] == "San Francisco"
        assert context["first_tag"] == "developer"

    @pytest.mark.asyncio
    async def test_handle_http_500_error(self, sut_config: SUTConfig) -> None:
        """Test handling HTTP 500 server error."""
        action = HttpAction(
            name="server-error",
            service="api",
            method="GET",
            path="/error",
        )

        mock_response = httpx.Response(
            status_code=500,
            json={"error": "Internal Server Error"},
            headers={"Content-Type": "application/json"},
        )
        # Set reason_phrase for error message
        mock_response._request = httpx.Request("GET", "https://api.example.com/error")

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.status_code == 500
        assert observation.body == {"error": "Internal Server Error"}
        assert len(observation.errors) > 0
        assert "500" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_handle_http_404_error(self, sut_config: SUTConfig) -> None:
        """Test handling HTTP 404 not found error."""
        action = HttpAction(
            name="not-found",
            service="api",
            method="GET",
            path="/nonexistent",
        )

        mock_response = httpx.Response(
            status_code=404,
            json={"error": "Not Found"},
            headers={"Content-Type": "application/json"},
        )
        mock_response._request = httpx.Request(
            "GET", "https://api.example.com/nonexistent"
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_timeout_error(self, sut_config: SUTConfig) -> None:
        """Test handling timeout error."""
        action = HttpAction(
            name="timeout-action",
            service="api",
            method="GET",
            path="/slow",
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("Request timed out"),
        ):
            observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.status_code is None
        assert len(observation.errors) > 0
        assert "timeout" in observation.errors[0].lower()

    @pytest.mark.asyncio
    async def test_handle_connection_error(self, sut_config: SUTConfig) -> None:
        """Test handling connection error."""
        action = HttpAction(
            name="connection-error",
            service="api",
            method="GET",
            path="/unreachable",
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.status_code is None
        assert len(observation.errors) > 0
        assert "error" in observation.errors[0].lower()

    @pytest.mark.asyncio
    async def test_latency_recording(self, sut_config: SUTConfig) -> None:
        """Test that latency is recorded correctly."""
        action = HttpAction(
            name="latency-test",
            service="api",
            method="GET",
            path="/users/123",
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        # Latency should be a positive number
        assert observation.latency_ms >= 0
        # Should be less than a few hundred ms for a mocked request
        assert observation.latency_ms < 1000

    @pytest.mark.asyncio
    async def test_headers_merging(self, sut_config: SUTConfig) -> None:
        """Test that headers are properly merged from default, service, and action."""
        action = HttpAction(
            name="headers-test",
            service="api",
            method="GET",
            path="/users/123",
            headers={"X-Action-Header": "action-value"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            await runner.execute({})

        call_kwargs = mock_request.call_args.kwargs
        headers = call_kwargs.get("headers", {})

        # Should have all three levels of headers
        assert headers.get("X-Default-Header") == "default-value"
        assert headers.get("X-Service-Header") == "service-value"
        assert headers.get("X-Action-Header") == "action-value"

    @pytest.mark.asyncio
    async def test_query_params(self, sut_config: SUTConfig) -> None:
        """Test that query parameters are passed correctly."""
        action = HttpAction(
            name="query-test",
            service="api",
            method="GET",
            path="/search",
            query={"q": "test", "limit": "10"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"results": []},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            await runner.execute({})

        call_kwargs = mock_request.call_args.kwargs
        params = call_kwargs.get("params", {})

        assert params.get("q") == "test"
        assert params.get("limit") == "10"

    @pytest.mark.asyncio
    async def test_context_preserved_on_update(self, sut_config: SUTConfig) -> None:
        """Test that existing context is preserved when adding extracted values."""
        action = HttpAction(
            name="context-test",
            service="api",
            method="GET",
            path="/users/123",
            extract={"user_id": "$.id"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)
        initial_context: dict[str, Any] = {"existing_key": "existing_value"}

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, updated_context = await runner.execute(initial_context)

        # Original context should be unchanged
        assert initial_context == {"existing_key": "existing_value"}
        # Updated context should have both
        assert updated_context["existing_key"] == "existing_value"
        assert updated_context["user_id"] == 123

    @pytest.mark.asyncio
    async def test_no_extraction_on_failed_request(
        self, sut_config: SUTConfig
    ) -> None:
        """Test that extraction is not attempted on failed requests."""
        action = HttpAction(
            name="no-extract-on-error",
            service="api",
            method="GET",
            path="/error",
            extract={"user_id": "$.id"},
        )

        mock_response = httpx.Response(
            status_code=500,
            json={"id": 123},  # Even if body has the value
            headers={"Content-Type": "application/json"},
        )
        mock_response._request = httpx.Request("GET", "https://api.example.com/error")

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is False
        # Should not extract values on failed request
        assert "user_id" not in context

    @pytest.mark.asyncio
    async def test_observation_model_fields(self, sut_config: SUTConfig) -> None:
        """Test that Observation model has all required fields."""
        action = HttpAction(
            name="observation-test",
            service="api",
            method="GET",
            path="/users/123",
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json", "X-Custom": "value"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        # Verify all required fields are present
        assert isinstance(observation, Observation)
        assert isinstance(observation.ok, bool)
        assert isinstance(observation.status_code, int)
        assert isinstance(observation.latency_ms, float)
        assert isinstance(observation.headers, dict)
        assert isinstance(observation.body, dict)
        assert isinstance(observation.errors, list)
        assert isinstance(observation.action_name, str)

    @pytest.mark.asyncio
    async def test_invalid_jsonpath_extraction(self, sut_config: SUTConfig) -> None:
        """Test handling of invalid JSONPath expressions."""
        action = HttpAction(
            name="invalid-jsonpath",
            service="api",
            method="GET",
            path="/users/123",
            extract={"bad_key": "invalid[[[path"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        # Should still succeed, but extraction should fail
        assert observation.ok is True
        assert "bad_key" not in context

    @pytest.mark.asyncio
    async def test_jsonpath_no_match(self, sut_config: SUTConfig) -> None:
        """Test handling when JSONPath doesn't match any values."""
        action = HttpAction(
            name="no-match",
            service="api",
            method="GET",
            path="/users/123",
            extract={"missing": "$.nonexistent.path"},
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        runner = HttpActionRunner(action=action, sut_config=sut_config)

        with patch.object(
            httpx.AsyncClient,
            "request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            observation, context = await runner.execute({})

        assert observation.ok is True
        assert "missing" not in context

    @pytest.mark.asyncio
    async def test_provided_client_is_used(self, sut_config: SUTConfig) -> None:
        """Test that a provided httpx client is used instead of creating new one."""
        action = HttpAction(
            name="client-test",
            service="api",
            method="GET",
            path="/users/123",
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123},
            headers={"Content-Type": "application/json"},
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=mock_response)

        runner = HttpActionRunner(
            action=action, sut_config=sut_config, client=mock_client
        )
        await runner.execute({})

        # Verify the provided client was used
        mock_client.request.assert_called_once()


class TestObservationModel:
    """Tests for the Observation model."""

    def test_observation_creation(self) -> None:
        """Test creating an Observation with all fields."""
        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=150.5,
            headers={"Content-Type": "application/json"},
            body={"id": 123},
            errors=[],
            action_name="test-action",
        )

        assert observation.ok is True
        assert observation.status_code == 200
        assert observation.latency_ms == 150.5
        assert observation.headers == {"Content-Type": "application/json"}
        assert observation.body == {"id": 123}
        assert observation.errors == []
        assert observation.action_name == "test-action"

    def test_observation_with_errors(self) -> None:
        """Test creating an Observation with errors."""
        observation = Observation(
            ok=False,
            status_code=500,
            latency_ms=100.0,
            errors=["HTTP 500: Internal Server Error"],
        )

        assert observation.ok is False
        assert observation.errors == ["HTTP 500: Internal Server Error"]

    def test_observation_without_status_code(self) -> None:
        """Test creating an Observation without status code (e.g., connection error)."""
        observation = Observation(
            ok=False,
            status_code=None,
            latency_ms=50.0,
            errors=["Connection refused"],
        )

        assert observation.ok is False
        assert observation.status_code is None

    def test_observation_default_values(self) -> None:
        """Test Observation default values."""
        observation = Observation(
            ok=True,
            latency_ms=100.0,
        )

        assert observation.status_code is None
        assert observation.headers == {}
        assert observation.body is None
        assert observation.errors == []
        assert observation.action_name == ""
