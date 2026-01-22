"""HTTP action runner for executing HTTP requests."""

import time
from typing import Any

import httpx
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

from windtunnel.actions.base import BaseActionRunner
from windtunnel.config.scenario import HttpAction
from windtunnel.config.sut import SUTConfig
from windtunnel.models.observation import Observation


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

        # Execute request with timing
        start_time = time.perf_counter()
        errors: list[str] = []
        response_headers: dict[str, str] = {}
        response_body: Any = None
        status_code: int | None = None
        ok = False

        try:
            if self._client is not None:
                response = await self._client.request(**request_kwargs)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.request(**request_kwargs)

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            status_code = response.status_code
            response_headers = dict(response.headers)

            # Parse response body
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            # Consider 2xx status codes as success
            ok = 200 <= status_code < 300

            if not ok:
                errors.append(f"HTTP {status_code}: {response.reason_phrase}")

        except httpx.TimeoutException as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            errors.append(f"Request timeout: {e}")
        except httpx.RequestError as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            errors.append(f"Request error: {e}")
        except Exception as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            errors.append(f"Unexpected error: {e}")

        # Create observation
        observation = Observation(
            ok=ok,
            status_code=status_code,
            latency_ms=latency_ms,
            headers=response_headers,
            body=response_body,
            errors=errors,
            action_name=self.action.name,
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
                errors.extend(extraction_errors)

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
