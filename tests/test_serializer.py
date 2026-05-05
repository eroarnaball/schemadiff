"""Tests for schemadiff.serializer module."""

import json
import pytest

from schemadiff.models import Column, Table, Schema
from schemadiff.serializer import (
    column_to_dict,
    table_to_dict,
    schema_to_dict,
    column_from_dict,
    table_from_dict,
    schema_from_dict,
    dump_schema,
    load_schema,
    dump_schema_file,
    load_schema_file,
)


def make_sample_schema() -> Schema:
    columns = [
        Column(name="id", data_type="INTEGER", nullable=False, primary_key=True),
        Column(name="email", data_type="VARCHAR(255)", nullable=False, default=None),
        Column(name="created_at", data_type="TIMESTAMP", nullable=True, default="NOW()"),
    ]
    table = Table(name="users", columns=columns)
    return Schema(name="public", tables=[table])


def test_column_to_dict():
    col = Column(name="id", data_type="INTEGER", nullable=False, primary_key=True)
    d = column_to_dict(col)
    assert d["name"] == "id"
    assert d["data_type"] == "INTEGER"
    assert d["nullable"] is False
    assert d["primary_key"] is True
    assert d["default"] is None


def test_column_from_dict_roundtrip():
    col = Column(name="score", data_type="FLOAT", nullable=True, default="0.0")
    assert column_from_dict(column_to_dict(col)) == col


def test_table_to_dict():
    schema = make_sample_schema()
    table = schema.tables[0]
    d = table_to_dict(table)
    assert d["name"] == "users"
    assert len(d["columns"]) == 3
    assert d["columns"][0]["name"] == "id"


def test_table_from_dict_roundtrip():
    schema = make_sample_schema()
    table = schema.tables[0]
    restored = table_from_dict(table_to_dict(table))
    assert restored.name == table.name
    assert len(restored.columns) == len(table.columns)
    assert restored.columns[0] == table.columns[0]


def test_schema_roundtrip_via_dict():
    schema = make_sample_schema()
    restored = schema_from_dict(schema_to_dict(schema))
    assert restored.name == schema.name
    assert len(restored.tables) == 1
    assert restored.tables[0].name == "users"


def test_dump_and_load_schema():
    schema = make_sample_schema()
    json_str = dump_schema(schema)
    data = json.loads(json_str)
    assert data["name"] == "public"
    assert data["tables"][0]["name"] == "users"

    restored = load_schema(json_str)
    assert restored.name == schema.name
    assert restored.tables[0].columns[1].data_type == "VARCHAR(255)"


def test_load_schema_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        load_schema("{not valid json")


def test_dump_and_load_schema_file(tmp_path):
    schema = make_sample_schema()
    path = str(tmp_path / "schema.json")
    dump_schema_file(schema, path)
    restored = load_schema_file(path)
    assert restored.name == schema.name
    assert len(restored.tables) == 1
    assert restored.tables[0].name == "users"
