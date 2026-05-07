"""Tests for schemadiff.change_log."""

import json
import os
import pytest

from schemadiff.change_log import (
    ChangeLogEntry,
    ChangeLogError,
    append_entry,
    build_entry,
    read_entries,
)


def _entry(label="v1", total=3, added=None, removed=None, modified=None):
    return ChangeLogEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        label=label,
        total_changes=total,
        tables_added=added or [],
        tables_removed=removed or [],
        tables_modified=modified or [],
    )


# --- ChangeLogEntry.to_dict / from_dict ---

def test_to_dict_contains_all_keys():
    e = _entry(label="rel-1", total=2, added=["users"])
    d = e.to_dict()
    assert d["label"] == "rel-1"
    assert d["total_changes"] == 2
    assert d["tables_added"] == ["users"]


def test_from_dict_roundtrip():
    original = _entry(label="v2", total=5, removed=["old_tbl"], modified=["orders"])
    restored = ChangeLogEntry.from_dict(original.to_dict())
    assert restored.label == original.label
    assert restored.total_changes == original.total_changes
    assert restored.tables_removed == ["old_tbl"]
    assert restored.tables_modified == ["orders"]


def test_from_dict_missing_field_raises():
    with pytest.raises(ChangeLogError, match="missing fields"):
        ChangeLogEntry.from_dict({"label": "x", "total_changes": 1})  # no timestamp


def test_from_dict_optional_lists_default_empty():
    e = ChangeLogEntry.from_dict(
        {"timestamp": "t", "label": "l", "total_changes": 0}
    )
    assert e.tables_added == []
    assert e.tables_removed == []
    assert e.tables_modified == []


# --- append_entry / read_entries ---

def test_append_and_read_single_entry(tmp_path):
    log = str(tmp_path / "changes.jsonl")
    e = _entry(label="v1", total=1)
    append_entry(log, e)
    entries = read_entries(log)
    assert len(entries) == 1
    assert entries[0].label == "v1"


def test_append_multiple_entries_preserves_order(tmp_path):
    log = str(tmp_path / "changes.jsonl")
    for i in range(3):
        append_entry(log, _entry(label=f"v{i}", total=i))
    entries = read_entries(log)
    assert [e.label for e in entries] == ["v0", "v1", "v2"]


def test_read_entries_missing_file_returns_empty(tmp_path):
    entries = read_entries(str(tmp_path / "nonexistent.jsonl"))
    assert entries == []


def test_read_entries_bad_json_raises(tmp_path):
    log = tmp_path / "bad.jsonl"
    log.write_text("not-json\n")
    with pytest.raises(ChangeLogError, match="Bad entry"):
        read_entries(str(log))


def test_append_creates_intermediate_dirs(tmp_path):
    log = str(tmp_path / "deep" / "nested" / "changes.jsonl")
    append_entry(log, _entry())
    assert os.path.exists(log)


# --- build_entry ---

def test_build_entry_from_summary_like_dict():
    summary = {
        "total_changes": 4,
        "tables_added": ["new_tbl"],
        "tables_removed": [],
        "tables_modified": ["orders", "users"],
    }
    e = build_entry("release-2", summary)
    assert e.label == "release-2"
    assert e.total_changes == 4
    assert e.tables_added == ["new_tbl"]
    assert e.tables_modified == ["orders", "users"]
    assert e.timestamp  # non-empty


def test_build_entry_calls_to_dict_if_available():
    class FakeSummary:
        def to_dict(self):
            return {"total_changes": 7, "tables_added": [], "tables_removed": [], "tables_modified": []}

    e = build_entry("v3", FakeSummary())
    assert e.total_changes == 7
