"""Tests for schemadiff.diff_sorter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pytest

from schemadiff.diff_sorter import (
    SortConfig,
    SortedEntry,
    sort_result,
    _collect_entries,
)


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------

@dataclass
class _ColDiff:
    old_type: str = "int"
    new_type: str = "int"
    old_nullable: bool = True
    new_nullable: bool = True


@dataclass
class _TableDiff:
    columns_added: List[str] = field(default_factory=list)
    columns_removed: List[str] = field(default_factory=list)
    columns_modified: Dict[str, _ColDiff] = field(default_factory=dict)


@dataclass
class _MockResult:
    tables_added: List[str] = field(default_factory=list)
    tables_removed: List[str] = field(default_factory=list)
    tables_modified: Dict[str, _TableDiff] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_collect_entries_empty():
    result = _MockResult()
    assert _collect_entries(result) == []


def test_collect_entries_table_added():
    result = _MockResult(tables_added=["users"])
    entries = _collect_entries(result)
    assert len(entries) == 1
    assert entries[0].change_type == "table_added"
    assert entries[0].table_name == "users"


def test_collect_entries_column_removed():
    td = _TableDiff(columns_removed=["email"])
    result = _MockResult(tables_modified={"orders": td})
    entries = _collect_entries(result)
    assert entries[0].change_type == "column_removed"
    assert entries[0].column_name == "email"


def test_collect_entries_type_changed():
    cd = _ColDiff(old_type="int", new_type="bigint")
    td = _TableDiff(columns_modified={"id": cd})
    result = _MockResult(tables_modified={"products": td})
    entries = _collect_entries(result)
    assert entries[0].change_type == "type_changed"
    assert "int" in entries[0].detail
    assert "bigint" in entries[0].detail


def test_collect_entries_nullable_changed():
    cd = _ColDiff(old_nullable=True, new_nullable=False)
    td = _TableDiff(columns_modified={"name": cd})
    result = _MockResult(tables_modified={"products": td})
    entries = _collect_entries(result)
    assert entries[0].change_type == "nullable_changed"


def test_sort_by_severity_ascending():
    result = _MockResult(
        tables_removed=["old_tbl"],
        tables_added=["new_tbl"],
    )
    entries = sort_result(result, SortConfig(key="severity", order="asc"))
    types = [e.change_type for e in entries]
    assert types.index("table_removed") < types.index("table_added")


def test_sort_by_table_name_ascending():
    result = _MockResult(tables_added=["zebra", "alpha", "mango"])
    entries = sort_result(result, SortConfig(key="table_name", order="asc", secondary_key=None))
    names = [e.table_name for e in entries]
    assert names == sorted(names, key=str.lower)


def test_sort_descending():
    result = _MockResult(tables_added=["a_table", "z_table"])
    entries = sort_result(result, SortConfig(key="table_name", order="desc", secondary_key=None))
    assert entries[0].table_name == "z_table"


def test_sorted_entry_to_dict():
    e = SortedEntry("users", "column_added", "email", None)
    d = e.to_dict()
    assert d["table_name"] == "users"
    assert d["change_type"] == "column_added"
    assert d["column_name"] == "email"
    assert d["detail"] is None


def test_default_sort_config():
    cfg = SortConfig()
    assert cfg.key == "severity"
    assert cfg.order == "asc"
    assert cfg.secondary_key == "table_name"
