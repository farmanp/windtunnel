"""HTTP action runner for executing HTTP requests."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

from turbulence.actions.base import BaseActionRunner
from turbulence.config.scenario import HttpAction
from turbulence.config.sut import SUTConfig
from turbulence.models.observation import Observation


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
        """Execute the HTTP action and return observation with updated context.

        Args:
            context: Current execution context with variables.

        Returns:
            A tuple of (Observation, updated_context) where updated_context
            contains any extracted values merged with the input context.
        """
        service = self.sut_config.get_service(self.action.service)
        base_url = str(service.base_url)
        url = f"{base_url}{self.action.path}"

        # Merge headers: default -> service -> action
        headers = {
            **self.sut_config.default_headers,
            **service.headers,
            **self.action.headers,
        }

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "method": self.action.method.upper(),
            "url": url,
            "headers": headers,
            "params": self.action.query if self.action.query else None,
            "timeout": service.timeout_seconds,
        }

        # Add JSON body if present
        if self.action.body is not None:
            request_kwargs["json"] = self.action.body

        # Determine retry configuration
        retry_config = self.action.retry
        max_attempts = retry_config.max_attempts if retry_config else 1
        
        # Track overall execution
        total_start_time = time.perf_counter()
        attempts: list[dict[str, Any]] = []
        
        # Variables to hold final state
        response_body: Any = None
        response_headers: dict[str, str] = {}
        status_code: int | None = None
        final_errors: list[str] = []
        ok = False

        for attempt_idx in range(1, max_attempts + 1):
            is_last_attempt = attempt_idx == max_attempts
            attempt_start = time.perf_counter()
            current_errors: list[str] = []
            should_retry = False
            
            try:
                if self._client is not None:
                    response = await self._client.request(**request_kwargs)
                else:
                    async with httpx.AsyncClient() as client:
                        response = await client.request(**request_kwargs)
                
                status_code = response.status_code
                response_headers = dict(response.headers)
                
                # Parse response body
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text

                ok = 200 <= status_code < 300
                
                if not ok:
                    current_errors.append(f"HTTP {status_code}: {response.reason_phrase}")
                    if retry_config and status_code in retry_config.on_status:
                        should_retry = True

            except httpx.TimeoutException as e:
                current_errors.append(f"Request timeout: {e}")
                if retry_config and retry_config.on_timeout:
                    should_retry = True
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                current_errors.append(f"Connection error: {e}")
                if retry_config and retry_config.on_connection_error:
                    should_retry = True
            except httpx.RequestError as e:
                current_errors.append(f"Request error: {e}")
                # Generic request errors usually not retried unless explicitly covered
            except Exception as e:
                current_errors.append(f"Unexpected error: {e}")

            attempt_duration = (time.perf_counter() - attempt_start) * 1000
            
            attempts.append({
                "attempt": attempt_idx,
                "status_code": status_code,
                "ok": ok,
                "latency_ms": attempt_duration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": current_errors[0] if current_errors else None
            })

            if ok:
                break
            
            if should_retry and not is_last_attempt:
                # Calculate backoff delay
                delay = 0.0
                if retry_config:
                    if retry_config.backoff == "fixed":
                        delay = retry_config.delay_ms / 1000.0
                    elif retry_config.backoff == "exponential":
                        # Exponential backoff: base * 2^(attempt-1)
                        # attempt_idx is 1-based. So 1->base, 2->2*base, etc.
                        # Wait, typically attempt 1 failed, we are about to start attempt 2.
                        # backoff factor usually applies to the retry count.
                        retry_count = attempt_idx
                        delay_ms = min(
                            retry_config.base_delay_ms * (2 ** (retry_count - 1)),
                            retry_config.max_delay_ms
                        )
                        delay = delay_ms / 1000.0
                
                await asyncio.sleep(delay)
            else:
                final_errors = current_errors
                break

        total_latency_ms = (time.perf_counter() - total_start_time) * 1000
        
        # Create observation
        observation = Observation(
            ok=ok,
            status_code=status_code,
            latency_ms=total_latency_ms,
            headers=response_headers,
            body=response_body,
            errors=final_errors,
            action_name=self.action.name,
            service=self.action.service,
            attempts=attempts,
        )

        # Extract values into context
        updated_context = dict(context)
        if ok and response_body is not None and self.action.extract:
            extraction_errors = self._extract_values(
                response_body,
                self.action.extract,
                updated_context,
            )
            if extraction_errors:
                observation.errors.extend(extraction_errors)

        return observation, updated_context

    def _extract_values(
        self,
        body: Any,
        extract_config: dict[str, str],
        context: dict[str, Any],
    ) -> list[str]:
        """Extract values from response body using JSONPath expressions.

        Args:
            body: The response body to extract from.
            extract_config: Mapping of context keys to JSONPath expressions.
            context: The context dictionary to update with extracted values.

        Returns:
            List of error messages for any failed extractions.
        """
        errors: list[str] = []

        for key, jsonpath_expr in extract_config.items():
            try:
                parsed_path = jsonpath_parse(jsonpath_expr)
                matches = parsed_path.find(body)

                if matches:
                    # Take the first match value
                    context[key] = matches[0].value
                else:
                    errors.append(
                        f"JSONPath '{jsonpath_expr}' did not match any values"
                    )
            except JsonPathParserError as e:
                errors.append(f"Invalid JSONPath '{jsonpath_expr}': {e}")
            except Exception as e:
                errors.append(f"Error extracting '{key}': {e}")

        return errors
