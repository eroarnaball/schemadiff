"""Tests for schemadiff.comparator module."""

import json
import pytest
from schemadiff.comparator import compare_schemas, compare_strings, compare_files, ComparisonResult
from schemadiff.models import Schema, Table, Column


def _make_schema(tables: dict) -> Schema:
    """Build a Schema from a plain dict: {table_name: {col_name: col_type}}."""
    schema_tables = {}
    for tname, cols in tables.items():
        columns = {cname: Column(name=cname, col_type=ctype) for cname, ctype in cols.items()}
        schema_tables[tname] = Table(name=tname, columns=columns)
    return Schema(tables=schema_tables)


def test_compare_schemas_no_changes():
    s = _make_schema({"users": {"id": "int", "name": "varchar"}})
    result = compare_schemas(s, s)
    assert isinstance(result, ComparisonResult)
    assert not result.has_changes
    assert result.tables_added == []
    assert result.tables_removed == []
    assert result.tables_modified == []


def test_compare_schemas_table_added():
    source = _make_schema({"users": {"id": "int"}})
    target = _make_schema({"users": {"id": "int"}, "orders": {"id": "int"}})
    result = compare_schemas(source, target)
    assert result.has_changes
    assert "orders" in result.tables_added
    assert result.tables_removed == []


def test_compare_schemas_table_removed():
    source = _make_schema({"users": {"id": "int"}, "logs": {"id": "int"}})
    target = _make_schema({"users": {"id": "int"}})
    result = compare_schemas(source, target)
    assert result.has_changes
    assert "logs" in result.tables_removed
    assert result.tables_added == []


def test_compare_schemas_column_modified():
    source = _make_schema({"users": {"id": "int", "name": "varchar"}})
    target = _make_schema({"users": {"id": "int", "name": "text"}})
    result = compare_schemas(source, target)
    assert result.has_changes
    assert "users" in result.tables_modified


def test_summary_no_changes():
    s = _make_schema({"users": {"id": "int"}})
    result = compare_schemas(s, s, source_name="prod", target_name="staging")
    summary = result.summary()
    assert "No schema drift" in summary
    assert "prod" in summary
    assert "staging" in summary


def test_summary_with_changes():
    source = _make_schema({"users": {"id": "int"}})
    target = _make_schema({"users": {"id": "int"}, "orders": {"id": "int"}})
    result = compare_schemas(source, target, source_name="v1", target_name="v2")
    summary = result.summary()
    assert "added" in summary
    assert "v1" in summary
    assert "v2" in summary


def test_compare_strings_basic():
    source_json = json.dumps({"tables": {"users": {"columns": {"id": {"type": "int"}}}}})
    target_json = json.dumps({"tables": {"users": {"columns": {"id": {"type": "int"}, "email": {"type": "varchar"}}}}})
    result = compare_strings(source_json, target_json, source_name="old", target_name="new")
    assert result.has_changes
    assert "users" in result.tables_modified


def test_compare_files(tmp_path):
    source_data = {"tables": {"users": {"columns": {"id": {"type": "int"}}}}}
    target_data = {"tables": {"users": {"columns": {"id": {"type": "int"}}}, "orders": {"columns": {"id": {"type": "int"}}}}}
    source_file = tmp_path / "source.json"
    target_file = tmp_path / "target.json"
    source_file.write_text(json.dumps(source_data))
    target_file.write_text(json.dumps(target_data))
    result = compare_files(str(source_file), str(target_file))
    assert result.has_changes
    assert "orders" in result.tables_added


def test_report_returns_string():
    source = _make_schema({"users": {"id": "int"}})
    target = _make_schema({"users": {"id": "bigint"}})
    result = compare_schemas(source, target)
    report = result.report()
    assert isinstance(report, str)
    assert len(report) > 0
