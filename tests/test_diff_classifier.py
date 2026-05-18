"""Tests for schemadiff.diff_classifier."""

from __future__ import annotations

import pytest
from schemadiff.diff_classifier import (
    ClassifiedEntry,
    ClassificationResult,
    classify_result,
    RISK_LEVELS,
)


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _ColDiff:
    def __init__(self, change_type, old_type=None, new_type=None, new_nullable=True):
        self.change_type = change_type
        self.old_type = old_type
        self.new_type = new_type
        self.new_nullable = new_nullable


class _TableDiff:
    def __init__(self, columns_changed=None):
        self.columns_changed = columns_changed or {}


class _MockResult:
    def __init__(self, added=(), removed=(), modified=None):
        self.tables_added = list(added)
        self.tables_removed = list(removed)
        self.tables_modified = modified or {}


# ---------------------------------------------------------------------------
# ClassifiedEntry
# ---------------------------------------------------------------------------

def test_classified_entry_to_dict():
    e = ClassifiedEntry("users", "table_added", None, "low", "New table")
    d = e.to_dict()
    assert d["table"] == "users"
    assert d["risk"] == "low"
    assert d["column"] is None


# ---------------------------------------------------------------------------
# ClassificationResult
# ---------------------------------------------------------------------------

def test_classification_result_by_risk():
    entries = [
        ClassifiedEntry("a", "table_added", None, "low", ""),
        ClassifiedEntry("b", "table_removed", None, "critical", ""),
    ]
    cr = ClassificationResult(entries=entries)
    assert len(cr.by_risk("low")) == 1
    assert len(cr.by_risk("critical")) == 1
    assert len(cr.by_risk("medium")) == 0


def test_classification_result_highest_risk():
    entries = [
        ClassifiedEntry("a", "column_added", "x", "low", ""),
        ClassifiedEntry("b", "column_type_changed", "y", "critical", ""),
    ]
    cr = ClassificationResult(entries=entries)
    assert cr.highest_risk() == "critical"


def test_classification_result_highest_risk_empty():
    assert ClassificationResult().highest_risk() is None


# ---------------------------------------------------------------------------
# classify_result
# ---------------------------------------------------------------------------

def test_classify_table_added_is_low():
    r = _MockResult(added=["orders"])
    cr = classify_result(r)
    assert len(cr.entries) == 1
    assert cr.entries[0].risk == "low"
    assert cr.entries[0].change_type == "table_added"


def test_classify_table_removed_is_critical():
    r = _MockResult(removed=["legacy"])
    cr = classify_result(r)
    assert cr.entries[0].risk == "critical"


def test_classify_column_added_nullable_low():
    td = _TableDiff(columns_changed={"email": _ColDiff("added", new_nullable=True)})
    r = _MockResult(modified={"users": td})
    cr = classify_result(r)
    assert cr.entries[0].risk == "low"


def test_classify_column_added_not_null_medium():
    td = _TableDiff(columns_changed={"code": _ColDiff("added", new_nullable=False)})
    r = _MockResult(modified={"orders": td})
    cr = classify_result(r)
    assert cr.entries[0].risk == "medium"


def test_classify_column_removed_high():
    td = _TableDiff(columns_changed={"ssn": _ColDiff("removed")})
    r = _MockResult(modified={"users": td})
    cr = classify_result(r)
    assert cr.entries[0].risk == "high"


def test_classify_type_change_critical():
    td = _TableDiff(columns_changed={
        "amount": _ColDiff("modified", old_type="integer", new_type="varchar")
    })
    r = _MockResult(modified={"payments": td})
    cr = classify_result(r)
    assert cr.entries[0].risk == "critical"


def test_classify_empty_result_no_entries():
    cr = classify_result(_MockResult())
    assert cr.entries == []
    assert cr.highest_risk() is None


def test_to_dict_structure():
    r = _MockResult(added=["foo"], removed=["bar"])
    d = classify_result(r).to_dict()
    assert "highest_risk" in d
    assert "total" in d
    assert "entries" in d
    assert d["total"] == 2
