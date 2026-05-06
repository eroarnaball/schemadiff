"""Schema validation module for schemadiff.

Provides validation of schema dictionaries before they are parsed,
ensuring required fields are present and values are of expected types.
"""

from typing import Any


VALID_COLUMN_TYPES = {
    "integer", "bigint", "smallint", "serial", "bigserial",
    "varchar", "char", "text", "boolean", "date", "timestamp",
    "timestamptz", "numeric", "decimal", "float", "double precision",
    "json", "jsonb", "uuid", "bytea",
}


class ValidationError(Exception):
    """Raised when a schema dict fails validation."""


def validate_column_dict(col: Any, context: str = "") -> None:
    """Validate a single column dictionary."""
    prefix = f"{context}: " if context else ""
    if not isinstance(col, dict):
        raise ValidationError(f"{prefix}column must be a dict, got {type(col).__name__}")
    if "name" not in col:
        raise ValidationError(f"{prefix}column missing required field 'name'")
    if not isinstance(col["name"], str) or not col["name"].strip():
        raise ValidationError(f"{prefix}column 'name' must be a non-empty string")
    if "type" not in col:
        raise ValidationError(f"{prefix}column '{col['name']}' missing required field 'type'")
    if not isinstance(col["type"], str):
        raise ValidationError(f"{prefix}column '{col['name']}' 'type' must be a string")
    if "nullable" in col and not isinstance(col["nullable"], bool):
        raise ValidationError(f"{prefix}column '{col['name']}' 'nullable' must be a bool")


def validate_table_dict(table: Any, context: str = "") -> None:
    """Validate a single table dictionary."""
    prefix = f"{context}: " if context else ""
    if not isinstance(table, dict):
        raise ValidationError(f"{prefix}table must be a dict, got {type(table).__name__}")
    if "name" not in table:
        raise ValidationError(f"{prefix}table missing required field 'name'")
    if not isinstance(table["name"], str) or not table["name"].strip():
        raise ValidationError(f"{prefix}table 'name' must be a non-empty string")
    columns = table.get("columns", [])
    if not isinstance(columns, list):
        raise ValidationError(f"{prefix}table '{table['name']}' 'columns' must be a list")
    for col in columns:
        validate_column_dict(col, context=f"{prefix}table '{table['name']}'")


def validate_schema_dict(schema: Any) -> None:
    """Validate a full schema dictionary."""
    if not isinstance(schema, dict):
        raise ValidationError(f"schema must be a dict, got {type(schema).__name__}")
    tables = schema.get("tables", [])
    if not isinstance(tables, list):
        raise ValidationError("'tables' must be a list")
    seen_names = set()
    for table in tables:
        validate_table_dict(table)
        name = table.get("name", "")
        if name in seen_names:
            raise ValidationError(f"duplicate table name: '{name}'")
        seen_names.add(name)
