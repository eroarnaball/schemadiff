"""Tests for the schema differ and reporter."""

import pytest

from schemadiff.differ import diff_schemas
from schemadiff.models import Column, Schema, Table
from schemadiff.reporter import format_diff


def make_schema(name: str, tables: list[Table]) -> Schema:
    return Schema(name=name, tables=tables)


def test_no_changes():
    col = Column(name="id", data_type="INTEGER", primary_key=True)
    table = Table(name="users", columns=[col])
    source = make_schema("v1", [table])
    target = make_schema("v2", [table])
    result = diff_schemas(source, target)
    assert not result.has_changes


def test_table_added():
    source = make_schema("v1", [])
    target = make_schema("v2", [Table(name="orders")])
    result = diff_schemas(source, target)
    assert result.has_changes
    assert len(result.table_diffs) == 1
    assert result.table_diffs[0].table == "orders"
    assert result.table_diffs[0].change == "added"


def test_table_removed():
    source = make_schema("v1", [Table(name="orders")])
    target = make_schema("v2", [])
    result = diff_schemas(source, target)
    assert result.has_changes
    assert result.table_diffs[0].change == "removed"


def test_column_added():
    col_id = Column(name="id", data_type="INTEGER")
    col_email = Column(name="email", data_type="VARCHAR")
    source = make_schema("v1", [Table(name="users", columns=[col_id])])
    target = make_schema("v2", [Table(name="users", columns=[col_id, col_email])])
    result = diff_schemas(source, target)
    assert result.has_changes
    table_diff = result.table_diffs[0]
    assert table_diff.change == "modified"
    assert len(table_diff.column_diffs) == 1
    assert table_diff.column_diffs[0].column == "email"
    assert table_diff.column_diffs[0].change == "added"


def test_column_type_modified():
    col_old = Column(name="age", data_type="INTEGER")
    col_new = Column(name="age", data_type="BIGINT")
    source = make_schema("v1", [Table(name="users", columns=[col_old])])
    target = make_schema("v2", [Table(name="users", columns=[col_new])])
    result = diff_schemas(source, target)
    assert result.has_changes
    col_diff = result.table_diffs[0].column_diffs[0]
    assert col_diff.change == "modified"
    assert col_diff.old_value.data_type == "INTEGER"
    assert col_diff.new_value.data_type == "BIGINT"


def test_format_diff_no_changes():
    source = make_schema("prod", [])
    target = make_schema("staging", [])
    result = diff_schemas(source, target)
    report = format_diff(result)
    assert "No changes detected" in report
    assert "prod" in report
    assert "staging" in report


def test_format_diff_with_changes():
    col = Column(name="id", data_type="INTEGER")
    source = make_schema("v1", [])
    target = make_schema("v2", [Table(name="events", columns=[col])])
    result = diff_schemas(source, target)
    report = format_diff(result)
    assert "+ TABLE" in report
    assert "events" in report
