"""Tests for assert action runner (FEAT-006)."""

import json
from pathlib import Path

import pytest

from windtunnel.actions.assert_ import AssertActionRunner
from windtunnel.config.scenario import AssertAction, Expectation
from windtunnel.models.assertion_result import AssertionResult


class TestStatusCodeAssertion:
    """Test status code assertions."""

    @pytest.mark.asyncio
    async def test_status_code_passes(self) -> None:
        """Status code assertion passes when codes match.

        Scenario: Status code assertion passes
        Given an assertion expecting status_code: 200
        And the last response had status code 200
        When the assertion evaluates
        Then the assertion passes
        And observation.ok is true
        """
        action = AssertAction(
            name="check_status",
            type="assert",
            expect=Expectation(status_code=200),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"message": "ok"},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is True
        assert observation.action_name == "check_status"
        assert not observation.errors

    @pytest.mark.asyncio
    async def test_status_code_fails(self) -> None:
        """Status code assertion fails when codes don't match.

        Scenario: Status code assertion fails
        Given an assertion expecting status_code: 200
        And the last response had status code 404
        When the assertion evaluates
        Then the assertion fails
        And observation includes expected: 200, actual: 404
        """
        action = AssertAction(
            name="check_status",
            type="assert",
            expect=Expectation(status_code=200),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 404,
                "body": {"error": "not found"},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is False
        assert len(observation.errors) == 1
        assert "expected 200" in observation.errors[0]
        assert "got 404" in observation.errors[0]

        # Check assertion result in context
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["passed"] is False
        assert assertion_result["expected"] == 200
        assert assertion_result["actual"] == 404

    @pytest.mark.asyncio
    async def test_status_code_missing_response(self) -> None:
        """Status code assertion fails when no response in context."""
        action = AssertAction(
            name="check_status",
            type="assert",
            expect=Expectation(status_code=200),
        )
        runner = AssertActionRunner(action)

        observation, updated_context = await runner.execute({})

        assert observation.ok is False
        assert "No last_response" in observation.errors[0]


class TestJsonPathAssertion:
    """Test JSONPath assertions."""

    @pytest.mark.asyncio
    async def test_jsonpath_equals_passes(self) -> None:
        """JSONPath equals assertion passes when values match.

        Scenario: JSONPath equals assertion
        Given an assertion with jsonpath: "$.total" equals: 100
        And the response body is {"total": 100, "items": 3}
        When the assertion evaluates
        Then the assertion passes
        """
        action = AssertAction(
            name="check_total",
            type="assert",
            expect=Expectation(jsonpath="$.total", equals=100),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"total": 100, "items": 3},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is True
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["passed"] is True
        assert assertion_result["expected"] == 100
        assert assertion_result["actual"] == 100
        assert assertion_result["path"] == "$.total"

    @pytest.mark.asyncio
    async def test_jsonpath_equals_fails(self) -> None:
        """JSONPath equals assertion fails when values don't match."""
        action = AssertAction(
            name="check_total",
            type="assert",
            expect=Expectation(jsonpath="$.total", equals=100),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"total": 50, "items": 3},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is False
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["expected"] == 100
        assert assertion_result["actual"] == 50

    @pytest.mark.asyncio
    async def test_jsonpath_contains_passes(self) -> None:
        """JSONPath contains assertion passes when value contains expected.

        Scenario: JSONPath contains assertion
        Given an assertion with jsonpath: "$.status" contains: "complete"
        And the response body is {"status": "order_complete"}
        When the assertion evaluates
        Then the assertion passes
        """
        action = AssertAction(
            name="check_status",
            type="assert",
            expect=Expectation(jsonpath="$.status", contains="complete"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"status": "order_complete"},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is True
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["passed"] is True
        assert assertion_result["comparison"] == "contains"

    @pytest.mark.asyncio
    async def test_jsonpath_contains_fails(self) -> None:
        """JSONPath contains assertion fails when value doesn't contain expected."""
        action = AssertAction(
            name="check_status",
            type="assert",
            expect=Expectation(jsonpath="$.status", contains="complete"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"status": "pending"},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is False
        assert "does not contain" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_jsonpath_nested(self) -> None:
        """JSONPath can access nested values."""
        action = AssertAction(
            name="check_user_name",
            type="assert",
            expect=Expectation(jsonpath="$.user.profile.name", equals="John"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {
                    "user": {
                        "profile": {"name": "John", "age": 30}
                    }
                },
            }
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_jsonpath_array_index(self) -> None:
        """JSONPath can access array elements."""
        action = AssertAction(
            name="check_first_item",
            type="assert",
            expect=Expectation(jsonpath="$.items[0].id", equals="item1"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {
                    "items": [
                        {"id": "item1", "name": "First"},
                        {"id": "item2", "name": "Second"},
                    ]
                },
            }
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_jsonpath_no_match(self) -> None:
        """JSONPath assertion fails when path doesn't match."""
        action = AssertAction(
            name="check_missing",
            type="assert",
            expect=Expectation(jsonpath="$.nonexistent", equals="value"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"data": "exists"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "matched no values" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_jsonpath_invalid_expression(self) -> None:
        """Invalid JSONPath expression reports error."""
        action = AssertAction(
            name="check_invalid",
            type="assert",
            expect=Expectation(jsonpath="$[invalid", equals="value"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"data": "exists"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "Invalid JSONPath" in observation.errors[0]


class TestContextPathAssertion:
    """Test context path assertions."""

    @pytest.mark.asyncio
    async def test_context_path_equals_passes(self) -> None:
        """Context path equals assertion passes when values match.

        Scenario: Assert on context values
        Given an assertion with context_path: "extracted_user_id" equals: 123
        And context["extracted_user_id"] is 123
        When the assertion evaluates
        Then the assertion passes
        """
        action = AssertAction(
            name="check_user_id",
            type="assert",
            expect=Expectation(context_path="extracted_user_id", equals=123),
        )
        runner = AssertActionRunner(action)

        context = {
            "extracted_user_id": 123,
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is True
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["passed"] is True
        assert assertion_result["expected"] == 123
        assert assertion_result["actual"] == 123
        assert assertion_result["path"] == "extracted_user_id"

    @pytest.mark.asyncio
    async def test_context_path_equals_fails(self) -> None:
        """Context path equals assertion fails when values don't match."""
        action = AssertAction(
            name="check_user_id",
            type="assert",
            expect=Expectation(context_path="extracted_user_id", equals=123),
        )
        runner = AssertActionRunner(action)

        context = {
            "extracted_user_id": 456,
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "expected 123" in observation.errors[0]
        assert "got 456" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_context_path_nested(self) -> None:
        """Context path can access nested values with dot notation."""
        action = AssertAction(
            name="check_nested",
            type="assert",
            expect=Expectation(context_path="user.profile.id", equals=42),
        )
        runner = AssertActionRunner(action)

        context = {
            "user": {
                "profile": {"id": 42, "name": "Test"}
            },
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_context_path_missing(self) -> None:
        """Context path assertion fails when path doesn't exist."""
        action = AssertAction(
            name="check_missing",
            type="assert",
            expect=Expectation(context_path="nonexistent", equals="value"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "not found in context" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_context_path_contains_in_string(self) -> None:
        """Context path contains works for strings."""
        action = AssertAction(
            name="check_message",
            type="assert",
            expect=Expectation(context_path="message", contains="success"),
        )
        runner = AssertActionRunner(action)

        context = {
            "message": "Operation completed successfully",
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_context_path_contains_in_list(self) -> None:
        """Context path contains works for lists."""
        action = AssertAction(
            name="check_tags",
            type="assert",
            expect=Expectation(context_path="tags", contains="important"),
        )
        runner = AssertActionRunner(action)

        context = {
            "tags": ["important", "urgent", "review"],
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True


class TestSchemaAssertion:
    """Test JSON Schema assertions."""

    @pytest.mark.asyncio
    async def test_schema_inline_passes(self) -> None:
        """Inline schema validation passes on matching response."""
        action = AssertAction(
            name="check_schema",
            type="assert",
            expect=Expectation(
                schema={
                    "type": "object",
                    "required": ["id", "status"],
                    "properties": {
                        "id": {"type": "integer"},
                        "status": {"type": "string"},
                    },
                }
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"id": 123, "status": "active"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_schema_missing_required_field_fails(self) -> None:
        """Schema validation fails with missing required field."""
        action = AssertAction(
            name="check_schema_required",
            type="assert",
            expect=Expectation(
                schema={
                    "type": "object",
                    "required": ["id", "status", "timestamp"],
                    "properties": {
                        "id": {"type": "integer"},
                        "status": {"type": "string"},
                        "timestamp": {"type": "string"},
                    },
                }
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"id": 123, "status": "active"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "timestamp" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_schema_type_mismatch_fails(self) -> None:
        """Schema validation fails with type mismatch."""
        action = AssertAction(
            name="check_schema_type",
            type="assert",
            expect=Expectation(
                schema={
                    "type": "object",
                    "properties": {"count": {"type": "integer"}},
                }
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"count": "five"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "integer" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_schema_ref_relative_to_scenario(self, tmp_path: Path) -> None:
        """$ref schema resolves relative to scenario file location."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        schema_file = schema_dir / "order.json"
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "required": ["id"],
                    "properties": {"id": {"type": "string"}},
                }
            )
        )

        scenario_path = tmp_path / "order.yaml"
        scenario_path.write_text("id: order")

        action = AssertAction(
            name="check_schema_ref",
            type="assert",
            expect=Expectation(schema={"$ref": "schemas/order.json"}),
        )
        runner = AssertActionRunner(action)

        context = {
            "_scenario_path": scenario_path,
            "last_response": {
                "status_code": 200,
                "body": {"id": "ord_123"},
            },
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_schema_nested_error_path(self) -> None:
        """Schema error message includes full JSON path."""
        action = AssertAction(
            name="check_schema_nested",
            type="assert",
            expect=Expectation(
                schema={
                    "type": "object",
                    "properties": {
                        "order": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "price": {"type": "number"}
                                        },
                                        "required": ["price"],
                                    },
                                }
                            },
                        }
                    },
                }
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"order": {"items": [{"price": "free"}]}},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "$.order.items[0].price" in observation.errors[0]


class TestExpressionAssertion:
    """Test expression-based assertions."""

    @pytest.mark.asyncio
    async def test_expression_sum_passes(self) -> None:
        """Expression passes when sum matches."""
        action = AssertAction(
            name="sum_check",
            type="assert",
            expect=Expectation(
                expression="sum([e['amount'] for e in body['entries']]) == 60"
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "body": {
                    "entries": [{"amount": 10}, {"amount": 20}, {"amount": 30}]
                }
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_expression_all_passes(self) -> None:
        """Expression passes when all items meet condition."""
        action = AssertAction(
            name="all_check",
            type="assert",
            expect=Expectation(
                expression="all(i['status'] == 'shipped' for i in body['items'])"
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "body": {"items": [{"status": "shipped"}, {"status": "shipped"}]}
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_expression_access_context(self) -> None:
        """Expression can access context variables."""
        action = AssertAction(
            name="context_check",
            type="assert",
            expect=Expectation(expression="body['total'] == context['expected_total']"),
        )
        runner = AssertActionRunner(action)

        context = {
            "expected_total": 100,
            "last_response": {"body": {"total": 100}},
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_expression_blocks_imports(self) -> None:
        """Expression blocks import attempts."""
        action = AssertAction(
            name="import_block",
            type="assert",
            expect=Expectation(expression="__import__('os').system('ls')"),
        )
        runner = AssertActionRunner(action)

        observation, _ = await runner.execute({"last_response": {"body": {}}})

        assert observation.ok is False
        assert "blocked" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_expression_blocks_file_access(self) -> None:
        """Expression blocks file access attempts."""
        action = AssertAction(
            name="file_block",
            type="assert",
            expect=Expectation(expression="open('/etc/passwd').read()"),
        )
        runner = AssertActionRunner(action)

        observation, _ = await runner.execute({"last_response": {"body": {}}})

        assert observation.ok is False
        assert "blocked" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_expression_timeout(self) -> None:
        """Expression times out on long-running evaluation."""
        action = AssertAction(
            name="timeout_check",
            type="assert",
            expect=Expectation(expression="sum(range(10**9))"),
        )
        runner = AssertActionRunner(action)

        observation, _ = await runner.execute({"last_response": {"body": {}}})

        assert observation.ok is False
        assert "timed out" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_expression_access_headers(self) -> None:
        """Expression can access response headers."""
        action = AssertAction(
            name="header_check",
            type="assert",
            expect=Expectation(
                expression="headers['X-Request-ID'].startswith('req_')"
            ),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "body": {},
                "headers": {"X-Request-ID": "req_123"},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is True


class TestNamedAssertions:
    """Test named assertions for reporting."""

    @pytest.mark.asyncio
    async def test_assertion_name_in_result(self) -> None:
        """Assertion name is included in result.

        Scenario: Named assertions in report
        Given an assertion with name: "payment_captured"
        When the assertion fails
        Then the failure is reported as "payment_captured" in results
        And the full path/expectation is included
        """
        action = AssertAction(
            name="payment_captured",
            type="assert",
            expect=Expectation(jsonpath="$.payment.status", equals="captured"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"payment": {"status": "pending"}},
            }
        }

        observation, updated_context = await runner.execute(context)

        assert observation.ok is False
        assert observation.action_name == "payment_captured"

        # Check assertion result includes full details
        assertion_result = updated_context["_last_assertion"]
        assert assertion_result["name"] == "payment_captured"
        assert assertion_result["path"] == "$.payment.status"
        assert assertion_result["expected"] == "captured"
        assert assertion_result["actual"] == "pending"

    @pytest.mark.asyncio
    async def test_multiple_assertions_tracked(self) -> None:
        """Multiple assertions are tracked in context."""
        action1 = AssertAction(
            name="first_check",
            type="assert",
            expect=Expectation(status_code=200),
        )
        action2 = AssertAction(
            name="second_check",
            type="assert",
            expect=Expectation(jsonpath="$.ok", equals=True),
        )

        runner1 = AssertActionRunner(action1)
        runner2 = AssertActionRunner(action2)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"ok": True},
            }
        }

        _, context = await runner1.execute(context)
        _, context = await runner2.execute(context)

        assert len(context["_assertion_results"]) == 2
        names = [r["name"] for r in context["_assertion_results"]]
        assert names == ["first_check", "second_check"]


class TestAssertionResultModel:
    """Test AssertionResult model."""

    def test_assertion_result_creation(self) -> None:
        """AssertionResult can be created with all fields."""
        result = AssertionResult(
            name="test_assertion",
            passed=True,
            expected=100,
            actual=100,
            message="Values match",
            path="$.total",
            comparison="equals",
        )

        assert result.name == "test_assertion"
        assert result.passed is True
        assert result.expected == 100
        assert result.actual == 100
        assert result.path == "$.total"
        assert result.comparison == "equals"

    def test_assertion_result_minimal(self) -> None:
        """AssertionResult can be created with minimal fields."""
        result = AssertionResult(
            name="minimal",
            passed=False,
        )

        assert result.name == "minimal"
        assert result.passed is False
        assert result.expected is None
        assert result.actual is None

    def test_assertion_result_to_dict(self) -> None:
        """AssertionResult can be converted to dict."""
        result = AssertionResult(
            name="test",
            passed=True,
            expected="value",
            actual="value",
        )

        data = result.model_dump()
        assert data["name"] == "test"
        assert data["passed"] is True


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_no_expectation_specified(self) -> None:
        """Assertion fails when no expectation is specified."""
        action = AssertAction(
            name="empty",
            type="assert",
            expect=Expectation(),
        )
        runner = AssertActionRunner(action)

        observation, _ = await runner.execute({})

        assert observation.ok is False
        assert "No expectation specified" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_jsonpath_with_no_comparison(self) -> None:
        """JSONPath without equals/contains fails."""
        action = AssertAction(
            name="no_compare",
            type="assert",
            expect=Expectation(jsonpath="$.value"),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"value": 123},
            }
        }

        observation, _ = await runner.execute(context)

        assert observation.ok is False
        assert "No comparison specified" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_observation_latency_tracked(self) -> None:
        """Observation includes latency measurement."""
        action = AssertAction(
            name="timing_test",
            type="assert",
            expect=Expectation(status_code=200),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {"status_code": 200, "body": {}},
        }

        observation, _ = await runner.execute(context)

        assert observation.latency_ms >= 0
        assert observation.latency_ms < 1000  # Should be very fast

    @pytest.mark.asyncio
    async def test_boolean_equals(self) -> None:
        """Boolean values are compared correctly."""
        action = AssertAction(
            name="check_bool",
            type="assert",
            expect=Expectation(jsonpath="$.active", equals=True),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"active": True},
            }
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_none_value_equals(self) -> None:
        """None/null values are compared correctly."""
        action = AssertAction(
            name="check_null",
            type="assert",
            expect=Expectation(jsonpath="$.deleted_at", equals=None),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"deleted_at": None},
            }
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True

    @pytest.mark.asyncio
    async def test_list_equals(self) -> None:
        """List values are compared correctly."""
        action = AssertAction(
            name="check_list",
            type="assert",
            expect=Expectation(jsonpath="$.tags", equals=["a", "b", "c"]),
        )
        runner = AssertActionRunner(action)

        context = {
            "last_response": {
                "status_code": 200,
                "body": {"tags": ["a", "b", "c"]},
            }
        }

        observation, _ = await runner.execute(context)
        assert observation.ok is True
