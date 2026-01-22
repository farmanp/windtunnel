"""JSON Schema validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import validators
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7


class SchemaValidationError(Exception):
    """Raised when JSON Schema validation fails."""

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message)
        self.path = path


def validate_json_schema(
    instance: Any,
    schema: dict[str, Any],
    *,
    base_path: Path | None = None,
) -> None:
    """Validate an instance against a JSON Schema.

    Args:
        instance: The data to validate.
        schema: JSON Schema definition (inline or with $ref).
        base_path: Optional base path to resolve $ref values.

    Raises:
        SchemaValidationError: If validation fails or schema is invalid.
    """
    validator_cls = validators.validator_for(schema)
    try:
        validator_cls.check_schema(schema)
    except Exception as exc:
        raise SchemaValidationError(f"Invalid JSON Schema: {exc}") from exc

    base_dir = None
    registry = Registry(retrieve=lambda uri: _retrieve_resource(uri, base_dir))
    if base_path is not None:
        base_dir = base_path if base_path.is_dir() else base_path.parent
        base_uri = base_dir.resolve().as_uri()
        if not base_uri.endswith("/"):
            base_uri = base_uri + "/"
        schema_with_id = schema
        if "$id" not in schema:
            schema_with_id = {**schema, "$id": base_uri}
        registry = registry.with_resource(
            base_uri,
            Resource.from_contents(schema_with_id, default_specification=DRAFT7),
        )

    validator = validator_cls(schema, registry=registry)
    error = next(validator.iter_errors(instance), None)
    if error is None:
        return

    path = _format_json_path(error.absolute_path)
    message = f"Schema validation failed at {path}: {error.message}"
    raise SchemaValidationError(message, path=path) from error


def _format_json_path(path_segments: Any) -> str:
    """Format a JSON path for error messages."""
    path = "$"
    for segment in list(path_segments):
        if isinstance(segment, int):
            path += f"[{segment}]"
        else:
            path += f".{segment}"
    return path


def _retrieve_resource(uri: str, base_dir: Path | None) -> Resource:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        path = Path(parsed.path)
    elif parsed.scheme == "" and base_dir is not None:
        path = base_dir / uri
    else:
        raise SchemaValidationError(f"Unsupported $ref URI scheme: {parsed.scheme}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(f"Schema $ref file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"Invalid JSON in schema file: {path}") from exc
    return Resource.from_contents(data, default_specification=DRAFT7)
