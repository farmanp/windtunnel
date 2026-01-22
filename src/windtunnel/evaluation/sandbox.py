"""Safe expression evaluation using AST validation and timeouts."""

from __future__ import annotations

import ast
import time
from collections.abc import Callable, Generator, Iterable
from typing import Any

ALLOWED_FUNCTIONS = {
    "sum",
    "len",
    "min",
    "max",
    "any",
    "all",
    "range",
}

ALLOWED_ATTRIBUTES = {
    "startswith",
    "endswith",
    "lower",
    "upper",
    "strip",
    "split",
    "get",
}


class ExpressionError(Exception):
    """Base error for expression evaluation failures."""


class ExpressionSecurityError(ExpressionError):
    """Raised when an expression violates sandbox rules."""


class ExpressionTimeoutError(ExpressionError):
    """Raised when an expression exceeds the evaluation timeout."""


class SafeExpressionEvaluator:
    """Evaluate expressions with a restrictive AST whitelist."""

    def __init__(self, timeout_seconds: float = 0.25) -> None:
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        expression: str,
        *,
        body: Any,
        headers: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> Any:
        """Evaluate a sandboxed Python expression.

        Args:
            expression: The expression to evaluate.
            body: Response body available to the expression.
            headers: Response headers available to the expression.
            context: Execution context available to the expression.

        Returns:
            The result of the evaluated expression.
        """
        try:
            _validate_expression(expression)
        except ExpressionError:
            raise

        controller = _TimeoutController(self.timeout_seconds)
        safe_locals = _build_safe_locals(
            body=body,
            headers=headers or {},
            context=context,
            controller=controller,
        )
        try:
            tree = ast.parse(expression, mode="eval")
            return eval(  # noqa: S307
                compile(tree, "<expression>", "eval"),
                {"__builtins__": {}},
                safe_locals,
            )
        except ExpressionTimeoutError:
            raise
        except ExpressionError:
            raise
        except Exception as exc:
            raise ExpressionError(f"Expression evaluation failed: {exc}") from exc


def _build_safe_locals(
    *,
    body: Any,
    headers: dict[str, Any],
    context: dict[str, Any],
    controller: _TimeoutController,
) -> dict[str, Any]:
    return {
        "body": body,
        "headers": headers,
        "context": context,
        "sum": _safe_sum(controller),
        "len": len,
        "min": _safe_min(controller),
        "max": _safe_max(controller),
        "any": _safe_any(controller),
        "all": _safe_all(controller),
        "range": _safe_range(controller),
    }


class _TimeoutController:
    def __init__(self, timeout_seconds: float) -> None:
        self._deadline = time.perf_counter() + timeout_seconds

    def check(self) -> None:
        if time.perf_counter() > self._deadline:
            raise ExpressionTimeoutError("Expression evaluation timed out")


def _safe_range(
    controller: _TimeoutController,
) -> Callable[..., Generator[int, None, None]]:
    def _range(*args: int) -> Generator[int, None, None]:
        for value in range(*args):
            controller.check()
            yield value

    return _range


def _safe_sum(controller: _TimeoutController) -> Callable[[Iterable[Any]], Any]:
    def _sum(values: Iterable[Any]) -> Any:
        total = 0
        for value in values:
            controller.check()
            total += value
        return total

    return _sum


def _safe_min(controller: _TimeoutController) -> Callable[[Iterable[Any]], Any]:
    def _min(values: Iterable[Any]) -> Any:
        iterator = iter(values)
        try:
            current = next(iterator)
        except StopIteration as exc:
            raise ValueError("min() arg is an empty sequence") from exc
        for value in iterator:
            controller.check()
            if value < current:
                current = value
        return current

    return _min


def _safe_max(controller: _TimeoutController) -> Callable[[Iterable[Any]], Any]:
    def _max(values: Iterable[Any]) -> Any:
        iterator = iter(values)
        try:
            current = next(iterator)
        except StopIteration as exc:
            raise ValueError("max() arg is an empty sequence") from exc
        for value in iterator:
            controller.check()
            if value > current:
                current = value
        return current

    return _max


def _safe_any(controller: _TimeoutController) -> Callable[[Iterable[Any]], bool]:
    def _any(values: Iterable[Any]) -> bool:
        for value in values:
            controller.check()
            if value:
                return True
        return False

    return _any


def _safe_all(controller: _TimeoutController) -> Callable[[Iterable[Any]], bool]:
    def _all(values: Iterable[Any]) -> bool:
        for value in values:
            controller.check()
            if not value:
                return False
        return True

    return _all


def _validate_expression(expression: str) -> None:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Invalid expression syntax: {exc}") from exc

    validator = _ExpressionValidator(
        allowed_names={
            "body",
            "headers",
            "context",
                *ALLOWED_FUNCTIONS,
            }
        )
    validator.visit(tree)


class _ExpressionValidator(ast.NodeVisitor):
    """AST validator enforcing a strict subset of Python expressions."""

    _allowed_nodes: tuple[type[ast.AST], ...] = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Set,
        ast.Subscript,
        ast.Attribute,
        ast.Slice,
        ast.IfExp,
        ast.ListComp,
        ast.GeneratorExp,
        ast.comprehension,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.FloorDiv,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
        ast.USub,
        ast.UAdd,
    )
    if hasattr(ast, "Index"):
        _allowed_nodes = _allowed_nodes + (ast.Index,)

    def __init__(self, *, allowed_names: set[str]) -> None:
        self._allowed_names = allowed_names

    def visit(self, node: ast.AST) -> Any:
        if not isinstance(node, self._allowed_nodes):
            raise ExpressionSecurityError(
                f"Disallowed expression node: {type(node).__name__}"
            )
        return super().visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self._allowed_names:
            raise ExpressionSecurityError(f"Disallowed name: {node.id}")
        return None

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr.startswith("__") or node.attr not in ALLOWED_ATTRIBUTES:
            raise ExpressionSecurityError(
                f"Attribute access not allowed: {node.attr}"
            )
        self.visit(node.value)
        return None

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Name):
            if node.func.id not in ALLOWED_FUNCTIONS:
                raise ExpressionSecurityError("Only approved functions may be called")
        elif isinstance(node.func, ast.Attribute):
            self.visit_Attribute(node.func)
        else:
            raise ExpressionSecurityError("Only approved functions may be called")
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)
        return None

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        self._visit_comprehension(node.elt, node.generators)
        return None

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Any:
        self._visit_comprehension(node.elt, node.generators)
        return None

    def _visit_comprehension(
        self,
        element: ast.AST,
        generators: Iterable[ast.comprehension],
    ) -> None:
        bound_names: list[str] = []
        for comp in generators:
            if not isinstance(comp.target, ast.Name):
                raise ExpressionSecurityError(
                    "Only simple names are allowed in comprehensions"
                )
            bound_names.append(comp.target.id)

        original = set(self._allowed_names)
        self._allowed_names.update(bound_names)

        for comp in generators:
            self.visit(comp.iter)
            for if_clause in comp.ifs:
                self.visit(if_clause)

        self.visit(element)
        self._allowed_names = original
