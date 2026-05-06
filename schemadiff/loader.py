"""Loader module for reading schema definitions from various sources."""

import json
import os
from typing import Union

from schemadiff.models import Schema
from schemadiff.serializer import schema_from_dict


def load_schema_from_file(path: str) -> Schema:
    """Load a schema from a JSON file on disk.

    Args:
        path: Absolute or relative path to a JSON schema file.

    Returns:
        A Schema instance populated from the file contents.

    Raises:
        FileNotFoundError: If the given path does not exist.
        ValueError: If the file cannot be parsed as a valid schema.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in schema file '{path}': {exc}") from exc

    return _parse_schema_dict(data, source=path)


def load_schema_from_string(content: str, source: str = "<string>") -> Schema:
    """Load a schema from a raw JSON string.

    Args:
        content: JSON string representing a schema.
        source:  Label used in error messages (e.g. a filename or tag).

    Returns:
        A Schema instance.

    Raises:
        ValueError: If the string cannot be parsed as a valid schema.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from source '{source}': {exc}") from exc

    return _parse_schema_dict(data, source=source)


def _parse_schema_dict(data: Union[dict, object], source: str) -> Schema:
    """Internal helper that validates the top-level structure and delegates
    to the serializer.

    Args:
        data:   Already-parsed Python object.
        source: Label used in error messages.

    Returns:
        A Schema instance.

    Raises:
        ValueError: If *data* is not a dict or is missing required keys.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Schema from '{source}' must be a JSON object, got {type(data).__name__}"
        )

    required_keys = {"name", "tables"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(
            f"Schema from '{source}' is missing required keys: {sorted(missing)}"
        )

    try:
        return schema_from_dict(data)
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Malformed schema from '{source}': {exc}") from exc
