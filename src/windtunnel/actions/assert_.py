"""Assert action runner for validating expectations."""

import time
from typing import Any

from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

from windtunnel.config.scenario import AssertAction, Expectation
from windtunnel.models.assertion_result import AssertionResult
from windtunnel.models.observation import Observation

# Sentinel object to distinguish "not set" from "set to None"
_NOT_SET = object()


class AssertActionRunner:
    """Runner for assert actions that validate expectations.

    Assert actions evaluate expectations against the current context,
    which includes the last HTTP response and any extracted values.
    """

    def __init__(self, action: AssertAction) -> None:
        """Initialize the assert action runner.

        Args:
            action: The assert action configuration.
        """
        self.action = action

    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the assertion and return observation.

        Args:
            context: Current execution context containing:
                - last_response: Dict with status_code, headers, body
                - Any extracted values from previous actions

        Returns:
            A tuple of (Observation, context) where observation.ok indicates
            whether all expectations passed.
        """
        start_time = time.perf_counter()

        result = self._evaluate_expectation(self.action.expect, context)

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Build observation
        observation = Observation(
            ok=result.passed,
            latency_ms=latency_ms,
            action_name=self.action.name,
            errors=[] if result.passed else [result.message],
        )

        # Store assertion result in context for reporting
        assertion_results = context.get("_assertion_results", [])
        assertion_results.append(result.model_dump())
        updated_context = {
            **context,
            "_assertion_results": assertion_results,
            "_last_assertion": result.model_dump(),
        }

        return observation, updated_context

    def _evaluate_expectation(
        self,
        expect: Expectation,
        context: dict[str, Any],
    ) -> AssertionResult:
        """Evaluate an expectation against the context.

        Args:
            expect: The expectation to evaluate.
            context: The current execution context.

        Returns:
            AssertionResult with pass/fail status and details.
        """
        # Status code assertion
        if expect.status_code is not None:
            return self._evaluate_status_code(expect, context)

        # JSONPath assertion
        if expect.jsonpath is not None:
            return self._evaluate_jsonpath(expect, context)

        # Context path assertion
        if expect.context_path is not None:
            return self._evaluate_context_path(expect, context)

        # No expectation specified
        return AssertionResult(
            name=self.action.name,
            passed=False,
            message=(
                "No expectation specified "
                "(need status_code, jsonpath, or context_path)"
            ),
        )

    def _evaluate_status_code(
        self,
        expect: Expectation,
        context: dict[str, Any],
    ) -> AssertionResult:
        """Evaluate status code expectation.

        Args:
            expect: Expectation with status_code.
            context: Context containing last_response.

        Returns:
            AssertionResult for status code comparison.
        """
        last_response = context.get("last_response", {})
        actual_status = last_response.get("status_code")

        if actual_status is None:
            return AssertionResult(
                name=self.action.name,
                passed=False,
                expected=expect.status_code,
                actual=None,
                message="No last_response in context or missing status_code",
                comparison="status_code",
            )

        passed = actual_status == expect.status_code

        if passed:
            message = (
                f"Status code {actual_status} matches expected {expect.status_code}"
            )
        else:
            message = (
                f"Status code mismatch: expected {expect.status_code}, "
                f"got {actual_status}"
            )

        return AssertionResult(
            name=self.action.name,
            passed=passed,
            expected=expect.status_code,
            actual=actual_status,
            message=message,
            comparison="status_code",
        )

    def _evaluate_jsonpath(
        self,
        expect: Expectation,
        context: dict[str, Any],
    ) -> AssertionResult:
        """Evaluate JSONPath expectation against response body.

        Args:
            expect: Expectation with jsonpath and equals/contains.
            context: Context containing last_response.

        Returns:
            AssertionResult for JSONPath comparison.
        """
        last_response = context.get("last_response", {})
        body = last_response.get("body")

        has_equals = "equals" in expect.model_fields_set
        has_contains = "contains" in expect.model_fields_set

        if body is None:
            return AssertionResult(
                name=self.action.name,
                passed=False,
                expected=expect.equals if has_equals else expect.contains,
                actual=None,
                message="No response body in context",
                path=expect.jsonpath,
                comparison="equals" if has_equals else "contains",
            )

        # Parse and evaluate JSONPath
        try:
            jsonpath_expr = jsonpath_parse(expect.jsonpath)
        except JsonPathParserError as e:
            return AssertionResult(
                name=self.action.name,
                passed=False,
                message=f"Invalid JSONPath expression '{expect.jsonpath}': {e}",
                path=expect.jsonpath,
            )

        matches = jsonpath_expr.find(body)

        if not matches:
            return AssertionResult(
                name=self.action.name,
                passed=False,
                expected=expect.equals if has_equals else expect.contains,
                actual=None,
                message=f"JSONPath '{expect.jsonpath}' matched no values in response",
                path=expect.jsonpath,
                comparison="equals" if has_equals else "contains",
            )

        # Get the first match value
        actual_value = matches[0].value

        return self._compare_values(
            actual=actual_value,
            expected_equals=expect.equals,
            expected_contains=expect.contains,
            path=expect.jsonpath,
            has_equals=has_equals,
            has_contains=has_contains,
        )

    def _evaluate_context_path(
        self,
        expect: Expectation,
        context: dict[str, Any],
    ) -> AssertionResult:
        """Evaluate context path expectation.

        Args:
            expect: Expectation with context_path and equals/contains.
            context: Context containing extracted values.

        Returns:
            AssertionResult for context value comparison.
        """
        context_path = expect.context_path
        has_equals = "equals" in expect.model_fields_set
        has_contains = "contains" in expect.model_fields_set

        # Handle nested paths with dot notation
        if context_path is None:
            return AssertionResult(
                name=self.action.name,
                passed=False,
                message="context_path is None",
                comparison="equals" if has_equals else "contains",
            )

        actual_value = self._get_nested_value(context, context_path)

        if actual_value is None and context_path not in context:
            # Check if it's truly missing or just has None value
            if not self._path_exists(context, context_path):
                return AssertionResult(
                    name=self.action.name,
                    passed=False,
                    expected=expect.equals if has_equals else expect.contains,
                    actual=None,
                    message=f"Context path '{context_path}' not found in context",
                    path=context_path,
                    comparison="equals" if has_equals else "contains",
                )

        return self._compare_values(
            actual=actual_value,
            expected_equals=expect.equals,
            expected_contains=expect.contains,
            path=context_path,
            has_equals=has_equals,
            has_contains=has_contains,
        )

    def _get_nested_value(
        self,
        data: dict[str, Any],
        path: str,
    ) -> Any:
        """Get a nested value from a dictionary using dot notation.

        Args:
            data: The dictionary to search.
            path: Dot-separated path (e.g., "user.profile.name").

        Returns:
            The value at the path, or None if not found.
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _path_exists(
        self,
        data: dict[str, Any],
        path: str,
    ) -> bool:
        """Check if a nested path exists in a dictionary.

        Args:
            data: The dictionary to search.
            path: Dot-separated path.

        Returns:
            True if the path exists (even if value is None).
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False

        return True

    def _compare_values(
        self,
        actual: Any,
        expected_equals: Any,
        expected_contains: Any,
        path: str | None,
        *,
        has_equals: bool,
        has_contains: bool,
    ) -> AssertionResult:
        """Compare actual value against expected using equals or contains.

        Args:
            actual: The actual value found.
            expected_equals: Value to compare for equality (if has_equals is True).
            expected_contains: Value to check for containment (if has_contains is True).
            path: The path that was evaluated (for error messages).
            has_equals: Whether equals comparison was explicitly specified.
            has_contains: Whether contains comparison was explicitly specified.

        Returns:
            AssertionResult for the comparison.
        """
        # Equals comparison
        if has_equals:
            passed = actual == expected_equals
            if passed:
                message = f"Value at '{path}' equals expected {expected_equals!r}"
            else:
                message = (
                    f"Value mismatch at '{path}': "
                    f"expected {expected_equals!r}, got {actual!r}"
                )
            return AssertionResult(
                name=self.action.name,
                passed=passed,
                expected=expected_equals,
                actual=actual,
                message=message,
                path=path,
                comparison="equals",
            )

        # Contains comparison
        if has_contains:
            try:
                if isinstance(actual, str):
                    passed = str(expected_contains) in actual
                elif isinstance(actual, (list, tuple)):
                    passed = expected_contains in actual
                elif isinstance(actual, dict):
                    passed = expected_contains in actual
                else:
                    passed = False
            except TypeError:
                passed = False

            if passed:
                message = f"Value at '{path}' contains {expected_contains!r}"
            else:
                message = (
                    f"Value at '{path}' does not contain {expected_contains!r}, "
                    f"actual: {actual!r}"
                )

            return AssertionResult(
                name=self.action.name,
                passed=passed,
                expected=expected_contains,
                actual=actual,
                message=message,
                path=path,
                comparison="contains",
            )

        # No comparison specified
        return AssertionResult(
            name=self.action.name,
            passed=False,
            actual=actual,
            message=(
                f"No comparison specified for path '{path}' "
                "(need equals or contains)"
            ),
            path=path,
        )
