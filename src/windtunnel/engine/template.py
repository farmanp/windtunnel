"""Template engine for variable substitution in workflows."""

import re
from typing import Any

from jinja2 import Environment, StrictUndefined, UndefinedError


class TemplateError(Exception):
    """Raised when template rendering fails."""

    def __init__(
        self, message: str, template: str, missing_var: str | None = None
    ) -> None:
        self.template = template
        self.missing_var = missing_var
        super().__init__(message)


class TemplateEngine:
    """Jinja2-based template engine for workflow variable substitution.

    Supports:
    - Simple substitution: {{user_id}}
    - Nested access: {{entry.seed_data.customer}}
    - Type preservation: numbers stay numbers when possible
    """

    # Pattern to detect if a string is ONLY a template variable (for type preservation)
    SINGLE_VAR_PATTERN = re.compile(r"^\{\{\s*[\w.]+\s*\}\}$")

    def __init__(self) -> None:
        """Initialize the template engine."""
        # Note: autoescape=False is intentional - we're rendering config values,
        # not HTML templates. XSS is not a concern for workflow variable substitution.
        self._env = Environment(
            undefined=StrictUndefined,
            autoescape=False,  # noqa: S701
            # Use standard {{ }} delimiters
            variable_start_string="{{",
            variable_end_string="}}",
        )

    def render_string(self, template: str, context: dict[str, Any]) -> Any:
        """Render a template string with context values.

        If the template is a single variable reference (e.g., "{{amount}}"),
        returns the value with its original type preserved.

        Args:
            template: The template string with {{variables}}
            context: Dictionary of variable values

        Returns:
            Rendered string, or original type if single variable

        Raises:
            TemplateError: If a variable is missing or template is invalid
        """
        if not isinstance(template, str):
            return template

        # Check if this is purely a single variable reference
        if self.SINGLE_VAR_PATTERN.match(template.strip()):
            # Extract the variable path
            var_path = template.strip()[2:-2].strip()
            try:
                return self._resolve_path(var_path, context)
            except KeyError as e:
                raise TemplateError(
                    f"Variable '{var_path}' not found in context",
                    template,
                    missing_var=var_path,
                ) from e

        # Otherwise, render as a string template
        try:
            jinja_template = self._env.from_string(template)
            return jinja_template.render(context)
        except UndefinedError as e:
            # Extract variable name from error message
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            raise TemplateError(
                f"Variable '{missing}' not found in context",
                template,
                missing_var=missing,
            ) from e

    def _resolve_path(self, path: str, context: dict[str, Any]) -> Any:
        """Resolve a dotted path in the context.

        Args:
            path: Dotted path like "entry.seed_data.customer"
            context: The context dictionary

        Returns:
            The resolved value

        Raises:
            KeyError: If any part of the path is not found
        """
        parts = path.split(".")
        current: Any = context

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    raise KeyError(part)
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                raise KeyError(part)

        return current

    def render_dict(
        self, data: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Render all template strings in a dictionary recursively.

        Args:
            data: Dictionary potentially containing template strings
            context: Variable values for substitution

        Returns:
            New dictionary with all templates rendered
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            result[key] = self.render_value(value, context)
        return result

    def render_list(self, data: list[Any], context: dict[str, Any]) -> list[Any]:
        """Render all template strings in a list recursively.

        Args:
            data: List potentially containing template strings
            context: Variable values for substitution

        Returns:
            New list with all templates rendered
        """
        return [self.render_value(item, context) for item in data]

    def render_value(self, value: Any, context: dict[str, Any]) -> Any:
        """Render a value, handling strings, dicts, and lists recursively.

        Args:
            value: Any value that might contain templates
            context: Variable values for substitution

        Returns:
            The value with all templates rendered
        """
        if isinstance(value, str):
            return self.render_string(value, context)
        elif isinstance(value, dict):
            return self.render_dict(value, context)
        elif isinstance(value, list):
            return self.render_list(value, context)
        else:
            # Numbers, bools, None, etc. pass through unchanged
            return value

    def has_templates(self, value: Any) -> bool:
        """Check if a value contains any template variables.

        Args:
            value: Value to check

        Returns:
            True if templates are found
        """
        if isinstance(value, str):
            return "{{" in value and "}}" in value
        elif isinstance(value, dict):
            return any(self.has_templates(v) for v in value.values())
        elif isinstance(value, list):
            return any(self.has_templates(v) for v in value)
        return False
