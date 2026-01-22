"""Condition evaluation for branching flows.

Two-phase evaluation:
1. Render templates: "{{payment_status}} == 'declined'" → "'approved' == 'declined'"
2. Evaluate expression using SafeExpressionEvaluator
"""

import logging
from typing import Any

from turbulence.engine.template import TemplateEngine, TemplateError
from turbulence.evaluation.sandbox import (
    ExpressionError,
    SafeExpressionEvaluator,
)

logger = logging.getLogger(__name__)


class ConditionEvaluationError(Exception):
    """Raised when condition evaluation fails."""

    def __init__(
        self,
        message: str,
        condition: str,
        rendered: str | None = None,
    ) -> None:
        self.condition = condition
        self.rendered = rendered
        super().__init__(message)


class ConditionEvaluator:
    """Evaluates boolean conditions for branching flows.

    Combines template rendering with safe expression evaluation to support
    conditions like "{{payment_status}} == 'declined'" that reference
    runtime context values.
    """

    def __init__(
        self,
        template_engine: TemplateEngine | None = None,
        expression_evaluator: SafeExpressionEvaluator | None = None,
    ) -> None:
        """Initialize the evaluator.

        Args:
            template_engine: Engine for rendering template variables.
            expression_evaluator: Evaluator for safe expression execution.
        """
        self.template_engine = template_engine or TemplateEngine()
        self.expression_evaluator = expression_evaluator or SafeExpressionEvaluator()

    def evaluate(
        self,
        condition: str,
        context: dict[str, Any],
    ) -> tuple[bool, str]:
        """Evaluate a condition against the execution context.

        Two-phase evaluation:
        1. Render templates in condition using context values
        2. Evaluate the rendered expression as a boolean

        Args:
            condition: Condition string with optional {{templates}}.
            context: Current execution context with extracted values.

        Returns:
            Tuple of (result, rendered_condition) for logging and debugging.

        Raises:
            ConditionEvaluationError: If evaluation fails.
        """
        if not condition:
            return True, ""

        # Phase 1: Render templates
        try:
            rendered = self._render_condition(condition, context)
        except TemplateError as e:
            logger.warning(
                f"Failed to render condition template '{condition}': {e}"
            )
            raise ConditionEvaluationError(
                f"Template rendering failed: {e}",
                condition=condition,
            ) from e

        # Handle simple boolean literals
        if rendered.strip().lower() in ("true", "1"):
            return True, rendered
        if rendered.strip().lower() in ("false", "0", ""):
            return False, rendered

        # Phase 2: Evaluate expression
        try:
            result = self._evaluate_expression(rendered, context)
            return bool(result), rendered
        except ExpressionError as e:
            logger.warning(
                f"Failed to evaluate condition '{condition}' "
                f"(rendered: '{rendered}'): {e}"
            )
            raise ConditionEvaluationError(
                f"Expression evaluation failed: {e}",
                condition=condition,
                rendered=rendered,
            ) from e

    def evaluate_safe(
        self,
        condition: str,
        context: dict[str, Any],
        default: bool = False,
    ) -> tuple[bool, str]:
        """Evaluate a condition, returning default on failure.

        Same as evaluate() but catches errors and returns default.
        Useful for optional conditions where failure should skip the action.

        Args:
            condition: Condition string with optional {{templates}}.
            context: Current execution context.
            default: Value to return on evaluation failure.

        Returns:
            Tuple of (result, rendered_condition).
        """
        try:
            return self.evaluate(condition, context)
        except ConditionEvaluationError as e:
            logger.error(
                f"Condition evaluation failed, using default={default}: {e}"
            )
            return default, e.rendered or condition

    def _render_condition(
        self,
        condition: str,
        context: dict[str, Any],
    ) -> str:
        """Render template variables in the condition.

        Args:
            condition: Raw condition with {{templates}}.
            context: Values for template substitution.

        Returns:
            Rendered condition string.
        """
        # Handle conditions that are entirely a template variable
        # e.g., "{{is_premium}}" should evaluate the boolean value directly
        rendered = self.template_engine.render_string(condition, context)

        # If the result is already a boolean or number, convert to string
        # for expression evaluation
        if isinstance(rendered, bool):
            return "True" if rendered else "False"
        if isinstance(rendered, (int, float)):
            return str(rendered)

        return str(rendered)

    def _evaluate_expression(
        self,
        expression: str,
        context: dict[str, Any],
    ) -> Any:
        """Evaluate a rendered expression.

        Args:
            expression: Rendered expression string.
            context: Context for the expression evaluator.

        Returns:
            Result of expression evaluation.
        """
        # Get last_response from context if available
        last_response = context.get("last_response", {})
        body = last_response.get("body")
        headers = last_response.get("headers", {})

        return self.expression_evaluator.evaluate(
            expression,
            body=body,
            headers=headers,
            context=context,
        )
