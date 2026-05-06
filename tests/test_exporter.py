"""Tests for schemadiff.exporter."""

import csv
import io
import json

import pytest

from schemadiff.models import Column, Table
from schemadiff.comparator import compare_schemas
from schemadiff.exporter import export_to_json, export_to_markdown, export_to_csv


def _make_schema(tables: dict):
    """Helper: build a minimal schema dict understood by compare_schemas."""
    from schemadiff.models import Schema  # noqa: F401 – imported for type only

    schema_tables = {}
    for tname, cols in tables.items():
        columns = {
            cname: Column(name=cname, **cdef)
            for cname, cdef in cols.items()
        }
        schema_tables[tname] = Table(name=tname, columns=columns)

    class _Schema:
        def __init__(self, t):
            self.tables = t

    return _Schema(schema_tables)


# ── JSON export ──────────────────────────────────────────────────────────────

def test_export_to_json_no_changes():
    s = _make_schema({"users": {"id": {"type": "int", "nullable": False}}})
    result = compare_schemas(s, s)
    payload = json.loads(export_to_json(result))
    assert payload["has_changes"] is False
    assert payload["tables_added"] == []
    assert payload["tables_removed"] == []
    assert payload["tables_modified"] == {}


def test_export_to_json_table_added():
    old = _make_schema({})
    new = _make_schema({"orders": {"id": {"type": "int", "nullable": False}}})
    result = compare_schemas(old, new)
    payload = json.loads(export_to_json(result))
    assert payload["has_changes"] is True
    assert "orders" in payload["tables_added"]


def test_export_to_json_column_modified():
    old = _make_schema({"users": {"email": {"type": "varchar(100)", "nullable": True}}})
    new = _make_schema({"users": {"email": {"type": "varchar(255)", "nullable": True}}})
    result = compare_schemas(old, new)
    payload = json.loads(export_to_json(result))
    assert "users" in payload["tables_modified"]
    assert "email" in payload["tables_modified"]["users"]["columns_modified"]


# ── Markdown export ──────────────────────────────────────────────────────────

def test_export_to_markdown_no_changes():
    s = _make_schema({"users": {"id": {"type": "int", "nullable": False}}})
    result = compare_schemas(s, s)
    md = export_to_markdown(result)
    assert "No schema changes" in md


def test_export_to_markdown_table_removed():
    old = _make_schema({"legacy": {"id": {"type": "int", "nullable": False}}})
    new = _make_schema({})
    result = compare_schemas(old, new)
    md = export_to_markdown(result)
    assert "Tables Removed" in md
    assert "`legacy`" in md


def test_export_to_markdown_column_added():
    old = _make_schema({"users": {"id": {"type": "int", "nullable": False}}})
    new = _make_schema({"users": {"id": {"type": "int", "nullable": False},
                                   "email": {"type": "text", "nullable": True}}})
    result = compare_schemas(old, new)
    md = export_to_markdown(result)
    assert "Added column" in md
    assert "`email`" in md


# ── CSV export ───────────────────────────────────────────────────────────────

def test_export_to_csv_headers():
    s = _make_schema({})
    result = compare_schemas(s, s)
    rows = list(csv.reader(io.StringIO(export_to_csv(result))))
    assert rows[0] == ["change_type", "table", "column", "detail"]


def test_export_to_csv_table_added_row():
    old = _make_schema({})
    new = _make_schema({"products": {"id": {"type": "int", "nullable": False}}})
    result = compare_schemas(old, new)
    rows = list(csv.reader(io.StringIO(export_to_csv(result))))
    data_rows = rows[1:]
    assert any(r[0] == "table_added" and r[1] == "products" for r in data_rows)


def test_export_to_csv_column_removed_row():
    old = _make_schema({"users": {"id": {"type": "int", "nullable": False},
                                   "bio": {"type": "text", "nullable": True}}})
    new = _make_schema({"users": {"id": {"type": "int", "nullable": False}}})
    result = compare_schemas(old, new)
    rows = list(csv.reader(io.StringIO(export_to_csv(result))))
    data_rows = rows[1:]
    assert any(r[0] == "column_removed" and r[2] == "bio" for r in data_rows)
