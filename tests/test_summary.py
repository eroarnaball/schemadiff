"""Tests for schemadiff.summary module."""

import pytest
from schemadiff.summary import SchemaSummary, summarize


class _ColDiff:
    def __init__(self, name, old, new):
        self.name = name
        self.old = old
        self.new = new


class _TableDiff:
    def __init__(self, name, columns_added=None, columns_removed=None, columns_modified=None):
        self.name = name
        self.columns_added = columns_added or []
        self.columns_removed = columns_removed or []
        self.columns_modified = columns_modified or []


class _MockResult:
    def __init__(self, added=None, removed=None, modified=None):
        self._added = added or []
        self._removed = removed or []
        self._modified = modified or []

    def tables_added(self):
        return iter(self._added)

    def tables_removed(self):
        return iter(self._removed)

    def tables_modified(self):
        return iter(self._modified)


def test_summary_no_changes():
    result = _MockResult()
    s = summarize(result)
    assert s.has_changes is False
    assert s.total_changes == 0
    assert s.tables_added == 0
    assert s.tables_removed == 0


def test_summary_tables_added():
    result = _MockResult(added=["users", "orders"])
    s = summarize(result)
    assert s.tables_added == 2
    assert s.has_changes is True
    assert s.total_changes == 2


def test_summary_tables_removed():
    result = _MockResult(removed=["legacy"])
    s = summarize(result)
    assert s.tables_removed == 1
    assert s.total_changes == 1


def test_summary_column_changes():
    td = _TableDiff(
        "users",
        columns_added=[_ColDiff("email", None, "varchar")],
        columns_removed=[_ColDiff("old_field", "int", None)],
        columns_modified=[_ColDiff("name", "varchar(50)", "varchar(100)")],
    )
    result = _MockResult(modified=[td])
    s = summarize(result)
    assert s.columns_added == 1
    assert s.columns_removed == 1
    assert s.columns_modified == 1
    assert s.total_changes == 3
    assert s.tables_modified == 1


def test_summary_to_dict_keys():
    result = _MockResult(added=["t1"])
    d = summarize(result).to_dict()
    expected_keys = {
        "total_tables_old", "total_tables_new", "tables_added",
        "tables_removed", "tables_modified", "tables_unchanged",
        "columns_added", "columns_removed", "columns_modified",
        "total_changes", "change_breakdown",
    }
    assert expected_keys == set(d.keys())


def test_summary_change_breakdown():
    td = _TableDiff("orders", columns_added=[_ColDiff("qty", None, "int")])
    result = _MockResult(removed=["old_table"], modified=[td])
    s = summarize(result)
    assert s.change_breakdown["tables_removed"] == 1
    assert s.change_breakdown["columns_added"] == 1


def test_schema_summary_defaults():
    s = SchemaSummary()
    assert s.total_changes == 0
    assert s.has_changes is False
    assert s.change_breakdown == {}
