"""Tests for schemadiff.diff_grouper."""
import pytest
from schemadiff.diff_grouper import group_result, GroupedResult


class _ColDiff:
    def __init__(self, column_name, added=False, removed=False, old_type=None, new_type=None):
        self.column_name = column_name
        self.added = added
        self.removed = removed
        self.old_type = old_type
        self.new_type = new_type


class _MockResult:
    def __init__(self, tables_added=None, tables_removed=None, column_changes=None):
        self.tables_added = tables_added or []
        self.tables_removed = tables_removed or []
        self.column_changes = column_changes or {}


def test_group_by_table_empty():
    result = group_result(_MockResult())
    assert isinstance(result, GroupedResult)
    assert result.groups == {}


def test_group_by_table_added_table():
    r = _MockResult(tables_added=["users", "orders"])
    grouped = group_result(r, group_by="table")
    assert "users" in grouped.groups
    assert "orders" in grouped.groups
    assert grouped.groups["users"].tables_added == ["users"]


def test_group_by_table_removed_table():
    r = _MockResult(tables_removed=["legacy"])
    grouped = group_result(r, group_by="table")
    assert "legacy" in grouped.groups
    assert grouped.groups["legacy"].tables_removed == ["legacy"]


def test_group_by_table_column_changes():
    col = _ColDiff("email", added=True)
    r = _MockResult(column_changes={"users": [col]})
    grouped = group_result(r, group_by="table")
    assert "users" in grouped.groups
    assert len(grouped.groups["users"].column_changes) == 1
    assert grouped.groups["users"].column_changes[0]["column"] == "email"


def test_group_by_severity_type_change_is_high():
    col = _ColDiff("age", old_type="int", new_type="varchar")
    r = _MockResult(column_changes={"users": [col]})
    grouped = group_result(r, group_by="severity")
    assert "high" in grouped.groups
    assert grouped.groups["high"].column_changes[0]["column"] == "age"


def test_group_by_severity_added_column_is_low():
    col = _ColDiff("nickname", added=True)
    r = _MockResult(column_changes={"users": [col]})
    grouped = group_result(r, group_by="severity")
    assert "low" in grouped.groups


def test_group_by_severity_removed_column_is_medium():
    col = _ColDiff("old_col", removed=True)
    r = _MockResult(column_changes={"users": [col]})
    grouped = group_result(r, group_by="severity")
    assert "medium" in grouped.groups


def test_group_by_change_type_column_added():
    col = _ColDiff("phone", added=True)
    r = _MockResult(column_changes={"users": [col]})
    grouped = group_result(r, group_by="change_type")
    assert "column_added" in grouped.groups


def test_group_by_change_type_table_added():
    r = _MockResult(tables_added=["payments"])
    grouped = group_result(r, group_by="change_type")
    assert "table_added" in grouped.groups
    assert "payments" in grouped.groups["table_added"].tables_added


def test_grouped_entry_total():
    col = _ColDiff("x", added=True)
    r = _MockResult(tables_added=["t1"], column_changes={"t2": [col, col]})
    grouped = group_result(r, group_by="table")
    assert grouped.groups["t1"].total() == 1
    assert grouped.groups["t2"].total() == 2


def test_to_dict_structure():
    col = _ColDiff("id", added=True)
    r = _MockResult(tables_added=["a"], column_changes={"b": [col]})
    grouped = group_result(r, group_by="table")
    d = grouped.to_dict()
    assert d["group_by"] == "table"
    assert "a" in d["groups"]
    assert "total" in d["groups"]["a"]
