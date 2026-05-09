"""Tests for schemadiff.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemadiff.auditor import (
    AuditEntry,
    AuditError,
    load_audit_log,
    record_comparison,
)
from schemadiff.models import Column, Table, Schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema(*table_names: str) -> "Schema":
    tables = {}
    for name in table_names:
        col = Column(name="id", col_type="integer", nullable=False)
        tables[name] = Table(name=name, columns={"id": col})
    return Schema(tables=tables)


class _FakeResult:
    """Minimal stand-in for a ComparisonResult."""

    def __init__(self, added=(), removed=(), modified=None):
        self.tables_added = list(added)
        self.tables_removed = list(removed)
        self.tables_modified = modified or {}


# ---------------------------------------------------------------------------
# AuditEntry.to_dict / from_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_required_keys():
    entry = AuditEntry(event="schema_comparison", source_label="a", target_label="b")
    d = entry.to_dict()
    for key in ("event", "source_label", "target_label", "timestamp", "hostname",
                "total_changes", "tables_added", "tables_removed",
                "columns_modified", "metadata"):
        assert key in d


def test_from_dict_roundtrip():
    entry = AuditEntry(
        event="schema_comparison",
        source_label="prod",
        target_label="staging",
        total_changes=3,
        tables_added=1,
        tables_removed=0,
        columns_modified=2,
        metadata={"env": "ci"},
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.event == entry.event
    assert restored.source_label == entry.source_label
    assert restored.total_changes == entry.total_changes
    assert restored.metadata == {"env": "ci"}


def test_from_dict_missing_field_raises():
    with pytest.raises(AuditError, match="missing fields"):
        AuditEntry.from_dict({"event": "schema_comparison"})


def test_from_dict_optional_fields_default():
    base = AuditEntry(event="e", source_label="s", target_label="t").to_dict()
    base.pop("total_changes")
    base.pop("metadata")
    entry = AuditEntry.from_dict(base)
    assert entry.total_changes == 0
    assert entry.metadata == {}


# ---------------------------------------------------------------------------
# record_comparison
# ---------------------------------------------------------------------------

def test_record_comparison_creates_file(tmp_path):
    log = tmp_path / "audit.log"
    result = _FakeResult(added=["orders"])
    record_comparison(result, "v1", "v2", log_path=log)
    assert log.exists()


def test_record_comparison_appends_valid_json(tmp_path):
    log = tmp_path / "audit.log"
    result = _FakeResult(added=["orders"], removed=["legacy"])
    record_comparison(result, "v1", "v2", log_path=log)
    record_comparison(result, "v2", "v3", log_path=log)
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert data["event"] == "schema_comparison"


def test_record_comparison_counts_added_removed(tmp_path):
    log = tmp_path / "audit.log"
    result = _FakeResult(added=["a", "b"], removed=["c"])
    entry = record_comparison(result, "src", "tgt", log_path=log)
    assert entry.tables_added == 2
    assert entry.tables_removed == 1


def test_record_comparison_metadata_stored(tmp_path):
    log = tmp_path / "audit.log"
    result = _FakeResult()
    entry = record_comparison(result, "s", "t", log_path=log, metadata={"run": "42"})
    assert entry.metadata == {"run": "42"}
    data = json.loads(log.read_text().strip())
    assert data["metadata"] == {"run": "42"}


def test_record_comparison_bad_path_raises():
    bad_log = Path("/no_such_root_dir_xyz/audit.log")
    result = _FakeResult()
    with pytest.raises(AuditError):
        record_comparison(result, "s", "t", log_path=bad_log)


# ---------------------------------------------------------------------------
# load_audit_log
# ---------------------------------------------------------------------------

def test_load_audit_log_empty_file(tmp_path):
    log = tmp_path / "audit.log"
    log.write_text("")
    assert load_audit_log(log) == []


def test_load_audit_log_missing_file(tmp_path):
    assert load_audit_log(tmp_path / "nonexistent.log") == []


def test_load_audit_log_returns_entries(tmp_path):
    log = tmp_path / "audit.log"
    result = _FakeResult(added=["x"])
    record_comparison(result, "a", "b", log_path=log)
    record_comparison(result, "b", "c", log_path=log)
    entries = load_audit_log(log)
    assert len(entries) == 2
    assert all(isinstance(e, AuditEntry) for e in entries)


def test_load_audit_log_invalid_json_raises(tmp_path):
    log = tmp_path / "audit.log"
    log.write_text("not json\n")
    with pytest.raises(AuditError, match="Invalid JSON"):
        load_audit_log(log)
