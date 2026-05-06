"""Tests for schemadiff.filter module."""

import pytest
from unittest.mock import MagicMock
from schemadiff.filter import filter_result, FilteredResult, _table_allowed


def _make_result(added=None, removed=None, modified=None):
    """Build a mock ComparisonResult."""
    result = MagicMock()
    result.tables_added.return_value = added or []
    result.tables_removed.return_value = removed or []
    result.tables_modified.return_value = modified or {}
    return result


def test_filter_no_restrictions_passes_all():
    result = _make_result(added=["users"], removed=["logs"], modified={"orders": object()})
    filtered = filter_result(result)
    assert filtered.tables_added() == ["users"]
    assert filtered.tables_removed() == ["logs"]
    assert "orders" in filtered.tables_modified()


def test_filter_include_tables():
    result = _make_result(added=["users", "posts"], removed=["logs"])
    filtered = filter_result(result, include_tables=["users"])
    assert filtered.tables_added() == ["users"]
    assert filtered.tables_removed() == []


def test_filter_exclude_tables():
    result = _make_result(added=["users", "posts"])
    filtered = filter_result(result, exclude_tables=["posts"])
    assert filtered.tables_added() == ["users"]


def test_filter_change_types_added_only():
    diff_obj = object()
    result = _make_result(added=["users"], removed=["logs"], modified={"orders": diff_obj})
    filtered = filter_result(result, change_types=["added"])
    assert filtered.tables_added() == ["users"]
    assert filtered.tables_removed() == []
    assert filtered.tables_modified() == {}


def test_filter_change_types_removed_only():
    result = _make_result(added=["users"], removed=["logs"])
    filtered = filter_result(result, change_types=["removed"])
    assert filtered.tables_added() == []
    assert filtered.tables_removed() == ["logs"]


def test_filter_change_types_modified_only():
    diff_obj = object()
    result = _make_result(added=["users"], modified={"orders": diff_obj})
    filtered = filter_result(result, change_types=["modified"])
    assert filtered.tables_added() == []
    assert "orders" in filtered.tables_modified()


def test_has_changes_true():
    result = _make_result(added=["users"])
    filtered = filter_result(result)
    assert filtered.has_changes() is True


def test_has_changes_false():
    result = _make_result()
    filtered = filter_result(result)
    assert filtered.has_changes() is False


def test_summary_no_changes():
    result = _make_result()
    filtered = filter_result(result)
    assert filtered.summary() == "no changes"


def test_summary_with_changes():
    diff_obj = object()
    result = _make_result(added=["users"], removed=["logs"], modified={"orders": diff_obj})
    filtered = filter_result(result)
    summary = filtered.summary()
    assert "added" in summary
    assert "removed" in summary
    assert "modified" in summary


def test_table_allowed_no_filters():
    assert _table_allowed("users", None, None) is True


def test_table_allowed_include_match():
    assert _table_allowed("users", ["users", "posts"], None) is True


def test_table_allowed_include_no_match():
    assert _table_allowed("logs", ["users", "posts"], None) is False


def test_table_allowed_exclude_match():
    assert _table_allowed("logs", None, ["logs"]) is False


def test_table_allowed_exclude_no_match():
    assert _table_allowed("users", None, ["logs"]) is True
