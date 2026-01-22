"""Tests for the wait action runner (FEAT-005)."""

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from pydantic import ValidationError

from windtunnel.actions.wait import (
    PollAttempt,
    WaitActionRunner,
    WaitObservation,
)
from windtunnel.config.scenario import Expectation, WaitAction
from windtunnel.config.sut import Service, SUTConfig


@pytest.fixture
def sut_config() -> SUTConfig:
    """Create a test SUTConfig."""
    return SUTConfig(
        name="test-sut",
        default_headers={"X-Api-Key": "test-key"},
        services={
            "api": Service(
                base_url="https://api.example.com",
                headers={"Accept": "application/json"},
                timeout_seconds=30.0,
            ),
        },
    )


class TestPollUntilConditionMet:
    """Test scenarios where the condition is eventually met."""

    @pytest.mark.asyncio
    async def test_condition_met_on_first_poll(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """First poll succeeds immediately - no unnecessary waiting."""
        action = WaitAction(
            name="wait_ready",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=1.0,
            timeout_seconds=10.0,
            expect=Expectation(jsonpath="$.ready", equals=True),
        )

        mock_response = httpx.Response(
            status_code=200,
            json={"ready": True},
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.total_attempts == 1
        assert observation.timed_out is False
        assert len(observation.attempts) == 1
        assert observation.attempts[0].condition_met is True
        # Should complete quickly without sleeping
        assert observation.latency_ms < 1000

    @pytest.mark.asyncio
    async def test_condition_met_after_multiple_polls(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Condition is met after several poll attempts."""
        action = WaitAction(
            name="wait_completed",
            type="wait",
            service="api",
            path="/orders/123",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.status", equals="completed"),
        )

        # Simulate: pending -> pending -> completed
        responses = [
            httpx.Response(200, json={"status": "pending"}),
            httpx.Response(200, json={"status": "pending"}),
            httpx.Response(200, json={"status": "completed"}),
        ]
        call_count = 0

        async def mock_request(**_kwargs: Any) -> httpx.Response:
            nonlocal call_count
            response = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return response

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.side_effect = mock_request

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.total_attempts == 3
        assert observation.timed_out is False
        assert observation.body == {"status": "completed"}
        # First two attempts should not meet condition
        assert observation.attempts[0].condition_met is False
        assert observation.attempts[1].condition_met is False
        # Third attempt should meet condition
        assert observation.attempts[2].condition_met is True


class TestTimeout:
    """Test timeout behavior when condition is never met."""

    @pytest.mark.asyncio
    async def test_timeout_when_condition_never_met(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Action times out when condition is never satisfied."""
        action = WaitAction(
            name="wait_timeout",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.1,
            timeout_seconds=0.35,
            expect=Expectation(jsonpath="$.status", equals="completed"),
        )

        mock_response = httpx.Response(200, json={"status": "pending"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True
        assert len(observation.errors) > 0
        assert "Timeout" in observation.errors[0]
        # Should have made at least 2 attempts
        assert observation.total_attempts >= 2

    @pytest.mark.asyncio
    async def test_all_attempts_recorded_on_timeout(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """All poll attempts are recorded even on timeout."""
        action = WaitAction(
            name="wait_record_all",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.05,
            timeout_seconds=0.2,
            expect=Expectation(jsonpath="$.done", equals=True),
        )

        mock_response = httpx.Response(200, json={"done": False})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True
        # Verify all attempts have required fields
        for attempt in observation.attempts:
            assert attempt.attempt_number > 0
            assert attempt.latency_ms >= 0
            assert attempt.timestamp_ms >= 0
            assert attempt.condition_met is False


class TestContainsComparison:
    """Test the 'contains' comparison operator."""

    @pytest.mark.asyncio
    async def test_contains_in_list(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Contains check works for list values."""
        action = WaitAction(
            name="wait_shipped",
            type="wait",
            service="api",
            path="/orders/123",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.tags", contains="shipped"),
        )

        mock_response = httpx.Response(
            200,
            json={"tags": ["pending", "shipped", "notified"]},
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.total_attempts == 1
        assert observation.attempts[0].condition_met is True

    @pytest.mark.asyncio
    async def test_contains_not_in_list(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Contains check fails when value not in list."""
        action = WaitAction(
            name="wait_delivered",
            type="wait",
            service="api",
            path="/orders/123",
            interval_seconds=0.05,
            timeout_seconds=0.15,
            expect=Expectation(jsonpath="$.tags", contains="delivered"),
        )

        mock_response = httpx.Response(
            200,
            json={"tags": ["pending", "shipped"]},
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True

    @pytest.mark.asyncio
    async def test_contains_in_string(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Contains check works for string values."""
        action = WaitAction(
            name="wait_message",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.message", contains="success"),
        )

        mock_response = httpx.Response(
            200,
            json={"message": "Operation completed with success"},
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True


class TestStatusCodeExpectation:
    """Test status code expectation matching."""

    @pytest.mark.asyncio
    async def test_status_code_match(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Wait succeeds when status code matches."""
        action = WaitAction(
            name="wait_status",
            type="wait",
            service="api",
            path="/health",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(status_code=200),
        )

        mock_response = httpx.Response(200, json={"status": "ok"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.status_code == 200

    @pytest.mark.asyncio
    async def test_status_code_mismatch_waits(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Wait continues when status code doesn't match."""
        action = WaitAction(
            name="wait_status_mismatch",
            type="wait",
            service="api",
            path="/health",
            interval_seconds=0.05,
            timeout_seconds=0.15,
            expect=Expectation(status_code=200),
        )

        mock_response = httpx.Response(503, json={"status": "unavailable"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True


class TestPollAttemptTracking:
    """Test that poll attempts are properly tracked."""

    @pytest.mark.asyncio
    async def test_attempt_details_recorded(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Each poll attempt has complete details."""
        action = WaitAction(
            name="wait_track",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.05,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.count", equals=3),
        )

        # Simulate incrementing count
        count = 0

        async def mock_request(**_kwargs: Any) -> httpx.Response:
            nonlocal count
            count += 1
            return httpx.Response(200, json={"count": count})

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.side_effect = mock_request

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.total_attempts == 3
        assert len(observation.attempts) == 3

        # Verify each attempt has proper data
        for i, attempt in enumerate(observation.attempts, start=1):
            assert attempt.attempt_number == i
            assert attempt.status_code == 200
            assert attempt.body == {"count": i}
            assert attempt.latency_ms > 0
            # Timestamps should be increasing
            if i > 1:
                assert attempt.timestamp_ms > observation.attempts[i - 2].timestamp_ms

        # Only the last attempt should have condition_met=True
        assert observation.attempts[-1].condition_met is True
        for attempt in observation.attempts[:-1]:
            assert attempt.condition_met is False


class TestErrorHandling:
    """Test error handling during polling."""

    @pytest.mark.asyncio
    async def test_request_timeout_recorded(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Request timeout errors are recorded in attempts."""
        action = WaitAction(
            name="wait_timeout_error",
            type="wait",
            service="api",
            path="/slow",
            interval_seconds=0.05,
            timeout_seconds=0.15,
            expect=Expectation(jsonpath="$.ready", equals=True),
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.side_effect = httpx.TimeoutException("Request timed out")

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True
        # Attempts should have error recorded
        for attempt in observation.attempts:
            assert attempt.error is not None
            assert "timeout" in attempt.error.lower()

    @pytest.mark.asyncio
    async def test_request_error_continues_polling(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Polling continues after request errors."""
        action = WaitAction(
            name="wait_error_recovery",
            type="wait",
            service="api",
            path="/flaky",
            interval_seconds=0.05,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.status", equals="ok"),
        )

        # Simulate: error -> error -> success
        call_count = 0

        async def mock_request(**_kwargs: Any) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection refused")
            return httpx.Response(200, json={"status": "ok"})

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.side_effect = mock_request

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True
        assert observation.total_attempts == 3
        # First two should have errors
        assert observation.attempts[0].error is not None
        assert observation.attempts[1].error is not None
        # Last one should succeed
        assert observation.attempts[2].error is None
        assert observation.attempts[2].condition_met is True


class TestJsonPathConditions:
    """Test various JSONPath condition scenarios."""

    @pytest.mark.asyncio
    async def test_nested_jsonpath(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """JSONPath works with nested objects."""
        action = WaitAction(
            name="wait_nested",
            type="wait",
            service="api",
            path="/order",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.order.status.phase", equals="shipped"),
        )

        mock_response = httpx.Response(
            200,
            json={"order": {"status": {"phase": "shipped", "timestamp": "2024-01-01"}}},
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_invalid_jsonpath_fails_condition(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Invalid JSONPath expressions fail the condition check."""
        action = WaitAction(
            name="wait_invalid_path",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.05,
            timeout_seconds=0.15,
            expect=Expectation(jsonpath="$[[[invalid", equals=True),
        )

        mock_response = httpx.Response(200, json={"ready": True})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True

    @pytest.mark.asyncio
    async def test_jsonpath_no_match_fails_condition(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """JSONPath that doesn't match fails the condition."""
        action = WaitAction(
            name="wait_no_match",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.05,
            timeout_seconds=0.15,
            expect=Expectation(jsonpath="$.nonexistent", equals=True),
        )

        mock_response = httpx.Response(200, json={"ready": True})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute({})

        assert observation.ok is False
        assert observation.timed_out is True


class TestContextHandling:
    """Test context handling in wait actions."""

    @pytest.mark.asyncio
    async def test_context_preserved(
        self,
        sut_config: SUTConfig,
    ) -> None:
        """Input context is preserved in output."""
        action = WaitAction(
            name="wait_context",
            type="wait",
            service="api",
            path="/status",
            interval_seconds=0.1,
            timeout_seconds=5.0,
            expect=Expectation(jsonpath="$.ready", equals=True),
        )

        mock_response = httpx.Response(200, json={"ready": True})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request.return_value = mock_response

        initial_context = {"user_id": "123", "order_id": "456"}
        runner = WaitActionRunner(action, sut_config, client=mock_client)
        observation, context = await runner.execute(initial_context)

        assert context["user_id"] == "123"
        assert context["order_id"] == "456"


class TestWaitObservationModel:
    """Test WaitObservation and PollAttempt models."""

    def test_wait_observation_creation(self) -> None:
        """WaitObservation can be created with all fields."""
        attempt = PollAttempt(
            attempt_number=1,
            timestamp_ms=0,
            latency_ms=50.0,
            status_code=200,
            body={"ready": True},
            condition_met=True,
        )

        observation = WaitObservation(
            ok=True,
            latency_ms=100.0,
            action_name="wait_test",
            attempts=[attempt],
            total_attempts=1,
            timed_out=False,
        )

        assert observation.ok is True
        assert observation.total_attempts == 1
        assert len(observation.attempts) == 1
        assert observation.attempts[0].condition_met is True

    def test_poll_attempt_validation(self) -> None:
        """PollAttempt validates required fields."""
        with pytest.raises(ValidationError):
            PollAttempt(
                attempt_number=0,  # Must be >= 1
                timestamp_ms=0,
                latency_ms=50.0,
            )
