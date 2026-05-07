"""Tests for schemadiff.snapshotter."""

import json
import os
import pytest

from schemadiff.models import Schema, Table, Column
from schemadiff.snapshotter import (
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    snapshot_to_dict,
    snapshot_from_dict,
    list_snapshots,
    SnapshotError,
)


def _make_schema() -> Schema:
    col = Column(name="id", col_type="integer", nullable=False)
    table = Table(name="users", columns=[col])
    return Schema(tables=[table])


def test_capture_snapshot_label():
    schema = _make_schema()
    snap = capture_snapshot(schema, label="v1")
    assert snap.label == "v1"
    assert snap.schema is schema
    assert snap.captured_at  # non-empty timestamp


def test_capture_snapshot_metadata():
    schema = _make_schema()
    snap = capture_snapshot(schema, label="v2", metadata={"env": "prod"})
    assert snap.metadata == {"env": "prod"}


def test_snapshot_to_dict_roundtrip():
    schema = _make_schema()
    snap = capture_snapshot(schema, label="test")
    d = snapshot_to_dict(snap)
    assert d["label"] == "test"
    assert "captured_at" in d
    assert "schema" in d
    restored = snapshot_from_dict(d)
    assert restored.label == snap.label
    assert restored.captured_at == snap.captured_at
    assert len(restored.schema.tables) == 1


def test_snapshot_from_dict_missing_field_raises():
    with pytest.raises(SnapshotError, match="Missing required snapshot field"):
        snapshot_from_dict({"label": "x"})


def test_save_and_load_snapshot(tmp_path):
    schema = _make_schema()
    snap = capture_snapshot(schema, label="saved")
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    assert os.path.exists(path)
    loaded = load_snapshot(path)
    assert loaded.label == "saved"
    assert len(loaded.schema.tables) == 1


def test_save_snapshot_creates_parent_dirs(tmp_path):
    schema = _make_schema()
    snap = capture_snapshot(schema, label="deep")
    path = str(tmp_path / "a" / "b" / "snap.json")
    save_snapshot(snap, path)
    assert os.path.exists(path)


def test_load_snapshot_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(str(tmp_path / "ghost.json"))


def test_load_snapshot_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with pytest.raises(SnapshotError, match="Invalid JSON"):
        load_snapshot(str(bad))


def test_list_snapshots_returns_sorted(tmp_path):
    schema = _make_schema()
    for name in ["c.json", "a.json", "b.json"]:
        snap = capture_snapshot(schema, label=name)
        save_snapshot(snap, str(tmp_path / name))
    paths = list_snapshots(str(tmp_path))
    basenames = [os.path.basename(p) for p in paths]
    assert basenames == ["a.json", "b.json", "c.json"]


def test_list_snapshots_empty_for_missing_dir():
    assert list_snapshots("/nonexistent/dir") == []
