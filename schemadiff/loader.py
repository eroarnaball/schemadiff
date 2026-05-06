"""Schema loading module for schemadiff.

Loads schema definitions from JSON files or strings and returns
parsed Schema model instances. Integrates validation before parsing.
"""

import json
from pathlib import Path
from typing import Union

from schemadiff.models import Column, Table, Schema
from schemadiff.validator import validate_schema_dict, ValidationError


class LoadError(Exception):
    """Raised when a schema cannot be loaded or parsed."""


def _parse_schema_dict(data: dict) -> "Schema":
    """Convert a validated schema dict into a Schema model."""
    tables = []
    for t in data.get("tables", []):
        columns = [
            Column(
                name=c["name"],
                col_type=c["type"],
                nullable=c.get("nullable", True),
                default=c.get("default"),
            )
            for c in t.get("columns", [])
        ]
        tables.append(Table(name=t["name"], columns=columns))
    return Schema(tables=tables)


def load_schema_from_string(text: str) -> "Schema":
    """Parse and validate a JSON string, returning a Schema.

    Raises:
        LoadError: if the text is not valid JSON, not a dict, or fails validation.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LoadError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise LoadError(f"Schema JSON must be an object, got {type(data).__name__}")

    try:
        validate_schema_dict(data)
    except ValidationError as exc:
        raise LoadError(f"Schema validation failed: {exc}") from exc

    return _parse_schema_dict(data)


def load_schema_from_file(path: Union[str, Path]) -> "Schema":
    """Read a JSON file and return a parsed Schema.

    Raises:
        LoadError: if the file cannot be read or the content is invalid.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LoadError(f"Cannot read file '{path}': {exc}") from exc
    return load_schema_from_string(text)
