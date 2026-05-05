"""Serialization and deserialization of schema objects to/from JSON."""

import json
from typing import Any

from schemadiff.models import Column, Table, Schema


def column_to_dict(column: Column) -> dict[str, Any]:
    """Serialize a Column to a dictionary."""
    return {
        "name": column.name,
        "data_type": column.data_type,
        "nullable": column.nullable,
        "default": column.default,
        "primary_key": column.primary_key,
    }


def table_to_dict(table: Table) -> dict[str, Any]:
    """Serialize a Table to a dictionary."""
    return {
        "name": table.name,
        "columns": [column_to_dict(col) for col in table.columns],
    }


def schema_to_dict(schema: Schema) -> dict[str, Any]:
    """Serialize a Schema to a dictionary."""
    return {
        "name": schema.name,
        "tables": [table_to_dict(t) for t in schema.tables],
    }


def column_from_dict(data: dict[str, Any]) -> Column:
    """Deserialize a Column from a dictionary."""
    return Column(
        name=data["name"],
        data_type=data["data_type"],
        nullable=data.get("nullable", True),
        default=data.get("default"),
        primary_key=data.get("primary_key", False),
    )


def table_from_dict(data: dict[str, Any]) -> Table:
    """Deserialize a Table from a dictionary."""
    columns = [column_from_dict(c) for c in data.get("columns", [])]
    return Table(name=data["name"], columns=columns)


def schema_from_dict(data: dict[str, Any]) -> Schema:
    """Deserialize a Schema from a dictionary."""
    tables = [table_from_dict(t) for t in data.get("tables", [])]
    return Schema(name=data.get("name", ""), tables=tables)


def dump_schema(schema: Schema, indent: int = 2) -> str:
    """Serialize a Schema to a JSON string."""
    return json.dumps(schema_to_dict(schema), indent=indent)


def load_schema(json_str: str) -> Schema:
    """Deserialize a Schema from a JSON string."""
    data = json.loads(json_str)
    return schema_from_dict(data)


def dump_schema_file(schema: Schema, path: str) -> None:
    """Write a Schema as JSON to a file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_schema(schema))


def load_schema_file(path: str) -> Schema:
    """Load a Schema from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return load_schema(f.read())
