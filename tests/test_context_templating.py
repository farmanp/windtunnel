"""Tests for context templating engine (FEAT-007)."""

import pytest

from windtunnel.engine import TemplateEngine, TemplateError, WorkflowContext


class TestTemplateEngineSimpleSubstitution:
    """Test simple variable substitution."""

    def test_substitute_simple_variable(self) -> None:
        """Substitute a simple variable in path."""
        engine = TemplateEngine()
        context = {"user_id": "usr_123"}
        result = engine.render_string("/users/{{user_id}}", context)
        assert result == "/users/usr_123"

    def test_substitute_multiple_variables(self) -> None:
        """Substitute multiple variables in one string."""
        engine = TemplateEngine()
        context = {"org": "acme", "user": "john"}
        result = engine.render_string("/orgs/{{org}}/users/{{user}}", context)
        assert result == "/orgs/acme/users/john"

    def test_variable_with_spaces(self) -> None:
        """Variables with spaces around them work."""
        engine = TemplateEngine()
        context = {"id": "123"}
        result = engine.render_string("{{ id }}", context)
        assert result == "123"


class TestTemplateEngineTypePreservation:
    """Test that types are preserved when possible."""

    def test_preserve_integer(self) -> None:
        """Single variable reference preserves integer type."""
        engine = TemplateEngine()
        context = {"amount": 100}
        result = engine.render_string("{{amount}}", context)
        assert result == 100
        assert isinstance(result, int)

    def test_preserve_float(self) -> None:
        """Single variable reference preserves float type."""
        engine = TemplateEngine()
        context = {"price": 29.99}
        result = engine.render_string("{{price}}", context)
        assert result == 29.99
        assert isinstance(result, float)

    def test_preserve_boolean(self) -> None:
        """Single variable reference preserves boolean type."""
        engine = TemplateEngine()
        context = {"active": True}
        result = engine.render_string("{{active}}", context)
        assert result is True
        assert isinstance(result, bool)

    def test_preserve_list(self) -> None:
        """Single variable reference preserves list type."""
        engine = TemplateEngine()
        context = {"items": [1, 2, 3]}
        result = engine.render_string("{{items}}", context)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_preserve_dict(self) -> None:
        """Single variable reference preserves dict type."""
        engine = TemplateEngine()
        context = {"data": {"key": "value"}}
        result = engine.render_string("{{data}}", context)
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_mixed_string_converts_to_string(self) -> None:
        """Variable mixed with text becomes string."""
        engine = TemplateEngine()
        context = {"amount": 100}
        result = engine.render_string("Total: {{amount}}", context)
        assert result == "Total: 100"
        assert isinstance(result, str)


class TestTemplateEngineNestedAccess:
    """Test nested access with dot notation."""

    def test_nested_dict_access(self) -> None:
        """Access nested dictionary values."""
        engine = TemplateEngine()
        context = {"entry": {"seed_data": {"customer": "cust_789"}}}
        result = engine.render_string("{{entry.seed_data.customer}}", context)
        assert result == "cust_789"

    def test_deeply_nested_access(self) -> None:
        """Access deeply nested values."""
        engine = TemplateEngine()
        context = {"a": {"b": {"c": {"d": "deep_value"}}}}
        result = engine.render_string("{{a.b.c.d}}", context)
        assert result == "deep_value"

    def test_nested_with_type_preservation(self) -> None:
        """Nested access preserves types."""
        engine = TemplateEngine()
        context = {"config": {"settings": {"count": 42}}}
        result = engine.render_string("{{config.settings.count}}", context)
        assert result == 42
        assert isinstance(result, int)


class TestTemplateEngineInJsonBody:
    """Test template substitution in JSON bodies."""

    def test_render_dict_with_templates(self) -> None:
        """Render templates in dictionary values."""
        engine = TemplateEngine()
        context = {"cart_id": "cart_456", "amount": 100}
        body = {"cart": "{{cart_id}}", "total": "{{amount}}"}
        result = engine.render_dict(body, context)
        assert result == {"cart": "cart_456", "total": 100}

    def test_render_nested_dict(self) -> None:
        """Render templates in nested dictionaries."""
        engine = TemplateEngine()
        context = {"user_id": "usr_1", "org_id": "org_2"}
        body = {
            "user": {"id": "{{user_id}}"},
            "organization": {"id": "{{org_id}}"},
        }
        result = engine.render_dict(body, context)
        assert result == {
            "user": {"id": "usr_1"},
            "organization": {"id": "org_2"},
        }

    def test_render_list_in_dict(self) -> None:
        """Render templates in lists inside dicts."""
        engine = TemplateEngine()
        context = {"item1": "apple", "item2": "banana"}
        body = {"items": ["{{item1}}", "{{item2}}"]}
        result = engine.render_dict(body, context)
        assert result == {"items": ["apple", "banana"]}

    def test_mixed_types_in_body(self) -> None:
        """Handle mixed types in body correctly."""
        engine = TemplateEngine()
        context = {"id": "123", "count": 5, "active": True}
        body = {
            "id": "{{id}}",
            "count": "{{count}}",
            "active": "{{active}}",
            "static": "unchanged",
            "number": 42,
        }
        result = engine.render_dict(body, context)
        assert result == {
            "id": "123",
            "count": 5,
            "active": True,
            "static": "unchanged",
            "number": 42,
        }


class TestTemplateEngineMissingVariables:
    """Test error handling for missing variables."""

    def test_missing_variable_raises_error(self) -> None:
        """Missing variable raises TemplateError."""
        engine = TemplateEngine()
        context = {"existing": "value"}
        with pytest.raises(TemplateError) as exc_info:
            engine.render_string("{{missing_key}}", context)
        assert "missing_key" in str(exc_info.value)
        assert exc_info.value.missing_var == "missing_key"

    def test_missing_nested_variable_raises_error(self) -> None:
        """Missing nested variable raises TemplateError."""
        engine = TemplateEngine()
        context = {"entry": {"other": "value"}}
        with pytest.raises(TemplateError):
            engine.render_string("{{entry.missing.path}}", context)

    def test_error_includes_template(self) -> None:
        """Error includes the original template."""
        engine = TemplateEngine()
        context = {}
        with pytest.raises(TemplateError) as exc_info:
            engine.render_string("/users/{{user_id}}/orders", context)
        assert exc_info.value.template == "/users/{{user_id}}/orders"


class TestTemplateEngineEdgeCases:
    """Test edge cases and special scenarios."""

    def test_no_templates_returns_original(self) -> None:
        """String without templates returns unchanged."""
        engine = TemplateEngine()
        result = engine.render_string("/static/path", {})
        assert result == "/static/path"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        engine = TemplateEngine()
        result = engine.render_string("", {})
        assert result == ""

    def test_none_value_passthrough(self) -> None:
        """None values pass through render_value unchanged."""
        engine = TemplateEngine()
        result = engine.render_value(None, {})
        assert result is None

    def test_number_passthrough(self) -> None:
        """Numbers pass through render_value unchanged."""
        engine = TemplateEngine()
        result = engine.render_value(42, {})
        assert result == 42

    def test_has_templates_detection(self) -> None:
        """has_templates correctly detects templates."""
        engine = TemplateEngine()
        assert engine.has_templates("{{var}}") is True
        assert engine.has_templates("no templates") is False
        assert engine.has_templates({"key": "{{var}}"}) is True
        assert engine.has_templates({"key": "static"}) is False
        assert engine.has_templates(["{{var}}"]) is True
        assert engine.has_templates(42) is False


class TestWorkflowContext:
    """Test WorkflowContext management."""

    def test_create_context_with_defaults(self) -> None:
        """Context creates with default IDs."""
        ctx = WorkflowContext()
        assert ctx.run_id.startswith("run_")
        assert ctx.instance_id.startswith("inst_")
        assert ctx.correlation_id.startswith("corr_")

    def test_set_entry_data(self) -> None:
        """Entry data can be set."""
        ctx = WorkflowContext()
        ctx.set_entry({"seed_data": {"email": "test@example.com"}})
        assert ctx.entry["seed_data"]["email"] == "test@example.com"

    def test_extract_values(self) -> None:
        """Extracted values are stored."""
        ctx = WorkflowContext()
        ctx.extract("order_id", "ord_001")
        assert ctx.get("order_id") == "ord_001"

    def test_extract_many(self) -> None:
        """Multiple values can be extracted at once."""
        ctx = WorkflowContext()
        ctx.extract_many({"id": "123", "name": "test"})
        assert ctx.get("id") == "123"
        assert ctx.get("name") == "test"

    def test_to_dict_for_templating(self) -> None:
        """to_dict produces correct structure for templating."""
        ctx = WorkflowContext(run_id="run_test", instance_id="inst_test")
        ctx.set_entry({"seed_data": {"user": "test_user"}})
        ctx.extract("cart_id", "cart_123")

        data = ctx.to_dict()
        assert data["run_id"] == "run_test"
        assert data["instance_id"] == "inst_test"
        assert data["entry"]["seed_data"]["user"] == "test_user"
        assert data["cart_id"] == "cart_123"

    def test_from_scenario_entry(self) -> None:
        """Create context from scenario entry block."""
        entry = {"seed_data": {"items": [1, 2, 3]}}
        ctx = WorkflowContext.from_scenario_entry(entry, run_id="run_001")
        assert ctx.run_id == "run_001"
        assert ctx.entry["seed_data"]["items"] == [1, 2, 3]

    def test_copy_preserves_extractions(self) -> None:
        """Copy preserves all extracted values."""
        ctx = WorkflowContext()
        ctx.extract("key", "value")
        copy = ctx.copy_with_extractions()
        assert copy.get("key") == "value"
        # Modifying copy doesn't affect original
        copy.extract("new_key", "new_value")
        assert ctx.get("new_key") is None


class TestContextWithTemplateEngine:
    """Test WorkflowContext integration with TemplateEngine."""

    def test_render_with_context(self) -> None:
        """Template engine works with context.to_dict()."""
        engine = TemplateEngine()
        ctx = WorkflowContext()
        ctx.set_entry({"seed_data": {"customer_id": "cust_123"}})
        ctx.extract("cart_id", "cart_456")

        template = "/customers/{{entry.seed_data.customer_id}}/carts/{{cart_id}}"
        result = engine.render_string(template, ctx.to_dict())
        assert result == "/customers/cust_123/carts/cart_456"

    def test_render_body_with_context(self) -> None:
        """Render JSON body with context values."""
        engine = TemplateEngine()
        ctx = WorkflowContext()
        ctx.extract("order_id", "ord_789")
        ctx.extract("amount", 150)

        body = {
            "order_id": "{{order_id}}",
            "payment": {"amount": "{{amount}}"},
        }
        result = engine.render_dict(body, ctx.to_dict())
        assert result == {
            "order_id": "ord_789",
            "payment": {"amount": 150},
        }

    def test_entry_block_population(self) -> None:
        """Entry block is accessible in templates."""
        engine = TemplateEngine()
        entry_data = {"seed_data": {"email": "test@example.com"}}
        ctx = WorkflowContext.from_scenario_entry(entry_data)

        result = engine.render_string(
            "{{entry.seed_data.email}}", ctx.to_dict()
        )
        assert result == "test@example.com"

    def test_run_and_correlation_ids_accessible(self) -> None:
        """Run and correlation IDs are accessible in templates."""
        engine = TemplateEngine()
        ctx = WorkflowContext(
            run_id="run_test123",
            correlation_id="corr_abc456",
        )

        headers = {
            "X-Run-ID": "{{run_id}}",
            "X-Correlation-ID": "{{correlation_id}}",
        }
        result = engine.render_dict(headers, ctx.to_dict())
        assert result == {
            "X-Run-ID": "run_test123",
            "X-Correlation-ID": "corr_abc456",
        }
