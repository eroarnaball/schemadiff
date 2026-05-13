"""Tests for schemadiff.differ_stats."""
from __future__ import annotations

import pytest

from schemadiff.differ_stats import DiffStats, compute_stats


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _ColDiff:
    def __init__(self, added: bool = False, removed: bool = False):
        self.added = added
        self.removed = removed


class _MockResult:
    def __init__(self, added=(), removed=(), modified=(), col_diffs=None):
        self._added = list(added)
        self._removed = list(removed)
        self._modified = list(modified)
        self._col_diffs: dict = col_diffs or {}

    def tables_added(self):
        return iter(self._added)

    def tables_removed(self):
        return iter(self._removed)

    def tables_modified(self):
        return iter(self._modified)

    def column_diffs(self, table_name):
        return iter(self._col_diffs.get(table_name, []))


# ---------------------------------------------------------------------------
# DiffStats unit tests
# ---------------------------------------------------------------------------

def test_diff_stats_defaults_are_zero():
    s = DiffStats()
    assert s.total_changes == 0
    assert s.total_table_changes == 0
    assert s.total_column_changes == 0


def test_diff_stats_totals():
    s = DiffStats(tables_added=1, tables_removed=2, tables_modified=3,
                  columns_added=4, columns_removed=5, columns_modified=6)
    assert s.total_table_changes == 6
    assert s.total_column_changes == 15
    assert s.total_changes == 21


def test_to_dict_has_all_keys():
    s = DiffStats(tables_added=1)
    d = s.to_dict()
    expected_keys = {
        "tables_added", "tables_removed", "tables_modified",
        "columns_added", "columns_removed", "columns_modified",
        "total_table_changes", "total_column_changes", "total_changes",
    }
    assert expected_keys == set(d.keys())


# ---------------------------------------------------------------------------
# compute_stats integration tests
# ---------------------------------------------------------------------------

def test_compute_stats_no_changes():
    result = _MockResult()
    stats = compute_stats(result)
    assert stats.total_changes == 0


def test_compute_stats_table_added_and_removed():
    result = _MockResult(added=["orders"], removed=["legacy"])
    stats = compute_stats(result)
    assert stats.tables_added == 1
    assert stats.tables_removed == 1
    assert stats.tables_modified == 0


def test_compute_stats_column_diffs():
    col_diffs = {
        "users": [
            _ColDiff(added=True),
            _ColDiff(removed=True),
            _ColDiff(),          # modified
        ]
    }
    result = _MockResult(modified=["users"], col_diffs=col_diffs)
    stats = compute_stats(result)
    assert stats.tables_modified == 1
    assert stats.columns_added == 1
    assert stats.columns_removed == 1
    assert stats.columns_modified == 1


def test_compute_stats_multiple_modified_tables():
    col_diffs = {
        "a": [_ColDiff(added=True), _ColDiff(added=True)],
        "b": [_ColDiff(removed=True)],
    }
    result = _MockResult(modified=["a", "b"], col_diffs=col_diffs)
    stats = compute_stats(result)
    assert stats.tables_modified == 2
    assert stats.columns_added == 2
    assert stats.columns_removed == 1
    assert stats.total_changes == 5  # 2 modified tables + 3 col changes
