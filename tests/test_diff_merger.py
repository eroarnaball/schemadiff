"""Tests for schemadiff.diff_merger."""
from __future__ import annotations

import pytest

from schemadiff.diff_merger import MergedResult, MergeError, merge_results


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, added=(), removed=(), col_changes=()):
        self.tables_added = list(added)
        self.tables_removed = list(removed)
        self.column_changes = list(col_changes)

    def has_changes(self):
        return bool(self.tables_added or self.tables_removed or self.column_changes)


# ---------------------------------------------------------------------------
# MergedResult unit tests
# ---------------------------------------------------------------------------

def test_merged_result_no_changes_has_changes_false():
    mr = MergedResult()
    assert mr.has_changes() is False


def test_merged_result_with_added_table_has_changes_true():
    mr = MergedResult()
    mr._tables_added.append("orders")
    assert mr.has_changes() is True


def test_merged_result_to_dict_keys():
    mr = MergedResult(sources=["a", "b"])
    mr._tables_added.append("users")
    d = mr.to_dict()
    assert set(d.keys()) == {"sources", "tables_added", "tables_removed", "column_changes", "has_changes"}
    assert d["has_changes"] is True
    assert d["tables_added"] == ["users"]


# ---------------------------------------------------------------------------
# merge_results tests
# ---------------------------------------------------------------------------

def test_merge_empty_raises():
    with pytest.raises(MergeError):
        merge_results([])


def test_merge_label_mismatch_raises():
    r = _FakeResult()
    with pytest.raises(MergeError):
        merge_results([r], labels=["a", "b"])


def test_merge_single_no_changes():
    r = _FakeResult()
    merged = merge_results([r])
    assert merged.has_changes() is False
    assert merged.sources == ["0"]


def test_merge_single_with_changes():
    r = _FakeResult(added=["orders"], removed=["legacy"])
    merged = merge_results([r], labels=["env-a"])
    assert merged.tables_added == ["orders"]
    assert merged.tables_removed == ["legacy"]
    assert merged.sources == ["env-a"]


def test_merge_deduplicates_table_added():
    r1 = _FakeResult(added=["orders", "users"])
    r2 = _FakeResult(added=["orders", "payments"])
    merged = merge_results([r1, r2])
    assert merged.tables_added.count("orders") == 1
    assert "users" in merged.tables_added
    assert "payments" in merged.tables_added


def test_merge_deduplicates_table_removed():
    r1 = _FakeResult(removed=["archive"])
    r2 = _FakeResult(removed=["archive", "temp"])
    merged = merge_results([r1, r2])
    assert merged.tables_removed.count("archive") == 1
    assert "temp" in merged.tables_removed


def test_merge_collects_all_column_changes():
    ch1 = {"table": "users", "column": "email", "change": "type"}
    ch2 = {"table": "orders", "column": "total", "change": "nullable"}
    r1 = _FakeResult(col_changes=[ch1])
    r2 = _FakeResult(col_changes=[ch2])
    merged = merge_results([r1, r2])
    assert len(merged.column_changes) == 2
    assert ch1 in merged.column_changes
    assert ch2 in merged.column_changes


def test_merge_preserves_labels():
    r1 = _FakeResult()
    r2 = _FakeResult()
    merged = merge_results([r1, r2], labels=["prod", "staging"])
    assert merged.sources == ["prod", "staging"]


def test_merge_to_dict_has_changes_false_when_empty():
    merged = merge_results([_FakeResult()])
    d = merged.to_dict()
    assert d["has_changes"] is False
