"""Wait action runner for polling until a condition is met."""

import asyncio
import time
from typing import Any

import httpx
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError
from pydantic import BaseModel, ConfigDict, Field

from turbulence.actions.base import BaseActionRunner
from turbulence.config.scenario import Expectation, WaitAction
from turbulence.config.sut import SUTConfig
from turbulence.models.observation import Observation


class PollAttempt(BaseModel):
    """Record of a single poll attempt during a wait action."""

    model_config = ConfigDict(extra="forbid")

    attempt_number: int = Field(
        ...,
        description="1-based attempt number",
        ge=1,
    )
    timestamp_ms: float = Field(
        ...,
        description="Timestamp in milliseconds since wait action started",
    )
    latency_ms: float = Field(
        ...,
        description="Latency of this poll attempt in milliseconds",
        ge=0,
    )
    status_code: int | None = Field(
        default=None,
        description="HTTP status code of the poll response",
    )
    body: Any = Field(
        default=None,
        description="Response body of the poll attempt",
    )
    condition_met: bool = Field(
        default=False,
        description="Whether the expected condition was met on this attempt",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the poll failed",
    )


class WaitObservation(Observation):
    """Extended observation for wait actions with poll attempt tracking."""

    model_config = ConfigDict(extra="forbid")

    attempts: list[PollAttempt] = Field(
        default_factory=list,
        description="List of all poll attempts made during the wait",
    )
    total_attempts: int = Field(
        default=0,
        description="Total number of poll attempts made",
        ge=0,
    )
    timed_out: bool = Field(
        default=False,
        description="Whether the wait action timed out",
    )


class WaitActionRunner(BaseActionRunner):
    """Executes wait actions by polling until a condition is met or timeout.

    This runner polls an endpoint at configurable intervals until an expected
    condition is satisfied or the timeout is reached. All poll attempts are
    recorded for observability.
    """

    def __init__(
        self,
        action: WaitAction,
        sut_config: SUTConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the wait action runner.

        Args:
            action: The wait action configuration to execute.
            sut_config: The system under test configuration.
            client: Optional httpx async client. If not provided, a new one
                will be created for each request.
        """
        self.action = action
        self.sut_config = sut_config
        self._client = client

    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[WaitObservation, dict[str, Any]]:
        """Execute the wait action by polling until condition met or timeout.

        Args:
            context: Current execution context with variables.

        Returns:
            A tuple of (WaitObservation, updated_context).
        """
        service = self.sut_config.get_service(self.action.service)
        base_url = str(service.base_url)
        url = f"{base_url}{self.action.path}"

        # Merge headers: default -> service
        headers = {
            **self.sut_config.default_headers,
            **service.headers,
        }

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "method": self.action.method.upper(),
            "url": url,
            "headers": headers,
            "timeout": min(service.timeout_seconds, self.action.timeout_seconds),
        }

        start_time = time.perf_counter()
        attempts: list[PollAttempt] = []
        attempt_number = 0
        condition_met = False
        last_body: Any = None
        last_status_code: int | None = None
        errors: list[str] = []
        timed_out = False

        while True:
            attempt_number += 1
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            elapsed_seconds = elapsed_ms / 1000

            # Check timeout before making request
            if elapsed_seconds >= self.action.timeout_seconds:
                timed_out = True
                errors.append(
                    f"Timeout after {elapsed_seconds:.1f}s "
                    f"({attempt_number - 1} attempts)"
                )
                break

            # Execute poll request
            poll_start = time.perf_counter()
            poll_error: str | None = None
            poll_body: Any = None
            poll_status_code: int | None = None

            try:
                if self._client is not None:
                    response = await self._client.request(**request_kwargs)
                else:
                    async with httpx.AsyncClient() as client:
                        response = await client.request(**request_kwargs)

                poll_status_code = response.status_code
                last_status_code = poll_status_code

                # Parse response body
                try:
                    poll_body = response.json()
                except Exception:
                    poll_body = response.text

                last_body = poll_body

            except httpx.TimeoutException as e:
                poll_error = f"Request timeout: {e}"
            except httpx.RequestError as e:
                poll_error = f"Request error: {e}"
            except Exception as e:
                poll_error = f"Unexpected error: {e}"

            poll_end = time.perf_counter()
            poll_latency_ms = (poll_end - poll_start) * 1000
            poll_timestamp_ms = (poll_start - start_time) * 1000

            # Check condition if no error
            if poll_error is None:
                condition_met = self._check_condition(
                    poll_body,
                    poll_status_code,
                    self.action.expect,
                )

            # Record attempt
            attempt = PollAttempt(
                attempt_number=attempt_number,
                timestamp_ms=poll_timestamp_ms,
                latency_ms=poll_latency_ms,
                status_code=poll_status_code,
                body=poll_body,
                condition_met=condition_met,
                error=poll_error,
            )
            attempts.append(attempt)

            # If condition met, we're done
            if condition_met:
                break

            # Wait before next poll, but check we won't exceed timeout
            remaining_seconds = self.action.timeout_seconds - elapsed_seconds
            sleep_time = min(self.action.interval_seconds, remaining_seconds)

            if sleep_time <= 0:
                timed_out = True
                errors.append(
                    f"Timeout after {elapsed_seconds:.1f}s ({attempt_number} attempts)"
                )
                break

            await asyncio.sleep(sleep_time)

        end_time = time.perf_counter()
        total_latency_ms = (end_time - start_time) * 1000

        # Create observation
        observation = WaitObservation(
            ok=condition_met,
            status_code=last_status_code,
            latency_ms=total_latency_ms,
            headers={},  # Not tracking headers for wait actions
            body=last_body,
            errors=errors,
            action_name=self.action.name,
            attempts=attempts,
            total_attempts=len(attempts),
            timed_out=timed_out,
        )

        return observation, dict(context)

    def _check_condition(
        self,
        body: Any,
        status_code: int | None,
        expect: Expectation,
    ) -> bool:
        """Check if the expected condition is met.

        Args:
            body: The response body to check.
            status_code: The HTTP status code.
            expect: The expectation configuration.

        Returns:
            True if all specified conditions are met, False otherwise.
        """
        # Check status code if specified
        if expect.status_code is not None:
            if status_code != expect.status_code:
                return False

        # Check JSONPath condition if specified
        if expect.jsonpath is not None:
            try:
                parsed_path = jsonpath_parse(expect.jsonpath)
                matches = parsed_path.find(body)

                if not matches:
                    return False

                value = matches[0].value

                # Check equals
                if expect.equals is not None:
                    if value != expect.equals:
                        return False

                # Check contains
                if expect.contains is not None:
                    if not self._check_contains(value, expect.contains):
                        return False

            except JsonPathParserError:
                return False
            except Exception:
                return False

        return True

    def _check_contains(self, value: Any, expected: Any) -> bool:
        """Check if value contains the expected value.

        Args:
            value: The value to check (list, string, dict, etc.)
            expected: The value to look for.

        Returns:
            True if value contains expected, False otherwise.
        """
        if isinstance(value, list):
            return expected in value
        if isinstance(value, str):
            return str(expected) in value
        if isinstance(value, dict):
            return expected in value.values()
        return False
