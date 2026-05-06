"""Tests for schemadiff.scorer."""

import pytest
from schemadiff.scorer import DriftScore, score_result, _WEIGHTS


# ---------------------------------------------------------------------------
# Minimal stubs that mimic the ComparisonResult interface
# ---------------------------------------------------------------------------

class _ColDiff:
    def __init__(self, added=False, removed=False):
        self.added = added
        self.removed = removed


class _MockResult:
    def __init__(self, added=(), removed=(), modified=None):
        self._added = list(added)
        self._removed = list(removed)
        self._modified = modified or {}  # {table_name: [_ColDiff, ...]}

    def tables_added(self):
        return iter(self._added)

    def tables_removed(self):
        return iter(self._removed)

    def tables_modified(self):
        return iter(self._modified.keys())

    def column_changes(self, table_name):
        return iter(self._modified.get(table_name, []))


# ---------------------------------------------------------------------------
# DriftScore tests
# ---------------------------------------------------------------------------

def test_severity_none():
    ds = DriftScore(total=0, breakdown={})
    assert ds.severity == "none"


def test_severity_low():
    ds = DriftScore(total=4, breakdown={})
    assert ds.severity == "low"


def test_severity_medium():
    ds = DriftScore(total=10, breakdown={})
    assert ds.severity == "medium"


def test_severity_high():
    ds = DriftScore(total=20, breakdown={})
    assert ds.severity == "high"


def test_to_dict_keys():
    ds = DriftScore(total=3, breakdown={"table_added": 3})
    d = ds.to_dict()
    assert set(d.keys()) == {"total", "severity", "breakdown"}
    assert d["total"] == 3


# ---------------------------------------------------------------------------
# score_result tests
# ---------------------------------------------------------------------------

def test_no_changes_score_zero():
    result = _MockResult()
    ds = score_result(result)
    assert ds.total == 0
    assert ds.severity == "none"


def test_table_added_score():
    result = _MockResult(added=["orders"])
    ds = score_result(result)
    assert ds.breakdown["table_added"] == _WEIGHTS["table_added"]


def test_table_removed_score():
    result = _MockResult(removed=["legacy"])
    ds = score_result(result)
    assert ds.breakdown["table_removed"] == _WEIGHTS["table_removed"]


def test_column_added_score():
    col_diffs = [_ColDiff(added=True)]
    result = _MockResult(modified={"users": col_diffs})
    ds = score_result(result)
    assert ds.breakdown["column_added"] == _WEIGHTS["column_added"]


def test_column_removed_score():
    col_diffs = [_ColDiff(removed=True)]
    result = _MockResult(modified={"users": col_diffs})
    ds = score_result(result)
    assert ds.breakdown["column_removed"] == _WEIGHTS["column_removed"]


def test_column_modified_score():
    col_diffs = [_ColDiff()]  # neither added nor removed => modified
    result = _MockResult(modified={"users": col_diffs})
    ds = score_result(result)
    assert ds.breakdown["column_modified"] == _WEIGHTS["column_modified"]


def test_mixed_changes_total():
    col_diffs = [_ColDiff(added=True), _ColDiff(removed=True)]
    result = _MockResult(
        added=["new_table"],
        removed=["old_table"],
        modified={"users": col_diffs},
    )
    ds = score_result(result)
    expected = (
        _WEIGHTS["table_added"]
        + _WEIGHTS["table_removed"]
        + _WEIGHTS["column_added"]
        + _WEIGHTS["column_removed"]
    )
    assert ds.total == expected
    assert ds.severity in ("medium", "high")
