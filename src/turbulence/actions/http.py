"""HTTP action runner for executing HTTP requests."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from turbulence.actions.base import BaseActionRunner
from turbulence.config.scenario import HttpAction
from turbulence.config.sut import SUTConfig
from turbulence.models.observation import Observation
from turbulence.utils.extractor import extract_values
from turbulence.utils.retry_policy import RetryConfig, with_retry


class HttpActionRunner(BaseActionRunner):
    """Executes HTTP actions and extracts values from responses.

    This runner handles HTTP requests with support for all standard HTTP methods,
    headers, query parameters, and JSON bodies. It also supports extracting
    values from responses using JSONPath expressions.
    """

    def __init__(
        self,
        action: HttpAction,
        sut_config: SUTConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the HTTP action runner.

        Args:
            action: The HTTP action configuration to execute.
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
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the HTTP action and return observation with updated context."""
        service = self.sut_config.get_service(self.action.service)
        base_url = str(service.base_url)
        url = f"{base_url}{self.action.path}"

        headers = {
            **self.sut_config.default_headers,
            **service.headers,
            **self.action.headers,
        }

        request_kwargs: dict[str, Any] = {
            "method": self.action.method.upper(),
            "url": url,
            "headers": headers,
            "params": self.action.query if self.action.query else None,
            "timeout": service.timeout_seconds,
        }

        if self.action.body is not None:
            request_kwargs["json"] = self.action.body

        attempts: list[dict[str, Any]] = []

        def on_attempt(idx: int, obs: Observation | None, exc: Exception | None, dur: float):
            status_code = obs.status_code if obs else None
            ok = obs.ok if obs else False
            error = None
            if exc:
                error = str(exc)
            elif obs and not obs.ok:
                error = obs.errors[0] if obs.errors else f"HTTP {status_code}"

            attempts.append({
                "attempt": idx,
                "status_code": status_code,
                "ok": ok,
                "latency_ms": dur,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error
            })

        # Configure retry
        max_attempts = 1
        retry_policy = None
        if self.action.retry:
            max_attempts = self.action.retry.max_attempts
            retry_policy = RetryConfig(
                max_attempts=max_attempts,
                strategy=self.action.retry.backoff,
                delay_seconds=self.action.retry.delay_ms / 1000.0 if self.action.retry.backoff == "fixed" else self.action.retry.base_delay_ms / 1000.0,
                max_delay_seconds=self.action.retry.max_delay_ms / 1000.0
            )
        else:
            retry_policy = RetryConfig(max_attempts=1, strategy="fixed")

        async def do_request() -> Observation:
            return await self._execute_single_request(request_kwargs)

        def is_retryable(e: Exception) -> bool:
            if not self.action.retry:
                return False
            if isinstance(e, httpx.TimeoutException):
                return self.action.retry.on_timeout
            if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                return self.action.retry.on_connection_error
            return False

        def should_retry_result(obs: Observation) -> bool:
            if not self.action.retry or not obs.status_code:
                return False
            return obs.status_code in self.action.retry.on_status

        total_start = time.perf_counter()
        try:
            observation = await with_retry(
                do_request,
                retry_policy,
                is_retryable=is_retryable,
                should_retry_result=should_retry_result,
                on_attempt=on_attempt
            )
        except Exception as e:
            # If all retries failed with exception, create a failure observation
            error_msg = str(e)
            if isinstance(e, httpx.TimeoutException):
                error_msg = f"Request timeout: {e}"
            elif isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
                error_msg = f"Connection error: {e}"
            elif isinstance(e, httpx.RequestError):
                error_msg = f"Request error: {e}"

            observation = Observation(
                ok=False,
                status_code=None,
                latency_ms=(time.perf_counter() - total_start) * 1000,
                headers={},
                body=None,
                errors=[error_msg],
                action_name=self.action.name,
                service=self.action.service,
                attempts=attempts,
            )

        observation.attempts = attempts
        observation.latency_ms = (time.perf_counter() - total_start) * 1000

        # Extraction logic
        updated_context = dict(context)
        if observation.ok and observation.body and self.action.extract:
            extracted = extract_values(observation.body, self.action.extract)
            updated_context.update(extracted)
            
            # Check for missing extractions to report as errors
            for key in self.action.extract:
                if key not in extracted:
                    observation.errors.append(f"JSONPath '{self.action.extract[key]}' did not match any values")

        return observation, updated_context

    async def _execute_single_request(self, request_kwargs: dict[str, Any]) -> Observation:
        """Execute a single HTTP request and return an Observation."""
        start_time = time.perf_counter()
        
        try:
            if self._client is not None:
                response = await self._client.request(**request_kwargs)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.request(**request_kwargs)
            
            status_code = response.status_code
            headers = dict(response.headers)
            
            try:
                body = response.json()
            except Exception:
                body = response.text

            ok = 200 <= status_code < 300
            errors = []
            if not ok:
                errors.append(f"HTTP {status_code}: {response.reason_phrase}")

            return Observation(
                ok=ok,
                status_code=status_code,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                headers=headers,
                body=body,
                errors=errors,
                action_name=self.action.name,
                service=self.action.service,
            )
        except Exception:
            # Re-raise to let with_retry handle it
            raise
