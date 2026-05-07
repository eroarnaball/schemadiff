"""Tests for schemadiff.snapshot_cli."""

import json
import os
import pytest

from schemadiff.snapshot_cli import build_snapshot_parser, run_snapshot_command
from schemadiff.snapshotter import capture_snapshot, save_snapshot
from schemadiff.models import Schema, Table, Column
from schemadiff.serializer import schema_to_dict


def _schema_payload(name="users") -> dict:
    return {
        "tables": [
            {
                "name": name,
                "columns": [{"name": "id", "type": "integer", "nullable": False}],
            }
        ]
    }


def _write_schema(path: str, payload: dict) -> None:
    with open(path, "w") as fh:
        json.dump(payload, fh)


def _parser():
    return build_snapshot_parser()


def test_capture_creates_snapshot_file(tmp_path):
    schema_file = str(tmp_path / "schema.json")
    snap_file = str(tmp_path / "snap.json")
    _write_schema(schema_file, _schema_payload())
    args = _parser().parse_args(["capture", schema_file, snap_file, "--label", "v1"])
    rc = run_snapshot_command(args)
    assert rc == 0
    assert os.path.exists(snap_file)
    with open(snap_file) as fh:
        data = json.load(fh)
    assert data["label"] == "v1"


def test_capture_missing_schema_returns_error(tmp_path):
    snap_file = str(tmp_path / "snap.json")
    args = _parser().parse_args(["capture", "/no/such/file.json", snap_file])
    rc = run_snapshot_command(args)
    assert rc == 1


def _make_and_save_snapshot(tmp_path, name, table_name="users"):
    col = Column(name="id", col_type="integer", nullable=False)
    table = Table(name=table_name, columns=[col])
    schema = Schema(tables=[table])
    snap = capture_snapshot(schema, label=name)
    path = str(tmp_path / f"{name}.json")
    save_snapshot(snap, path)
    return path


def test_diff_no_changes_exit_zero(tmp_path):
    before = _make_and_save_snapshot(tmp_path, "before")
    after = _make_and_save_snapshot(tmp_path, "after")
    args = _parser().parse_args(["diff", before, after])
    rc = run_snapshot_command(args)
    assert rc == 0


def test_diff_with_changes_exit_one(tmp_path):
    before = _make_and_save_snapshot(tmp_path, "before", table_name="users")
    after = _make_and_save_snapshot(tmp_path, "after", table_name="orders")
    args = _parser().parse_args(["diff", before, after])
    rc = run_snapshot_command(args)
    assert rc == 1


def test_diff_json_format_output(tmp_path, capsys):
    before = _make_and_save_snapshot(tmp_path, "before")
    after = _make_and_save_snapshot(tmp_path, "after", table_name="orders")
    args = _parser().parse_args(["diff", before, after, "--format", "json"])
    run_snapshot_command(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_list_snapshots_command(tmp_path):
    _make_and_save_snapshot(tmp_path, "snap1")
    _make_and_save_snapshot(tmp_path, "snap2")
    args = _parser().parse_args(["list", str(tmp_path)])
    rc = run_snapshot_command(args)
    assert rc == 0


def test_list_snapshots_empty_dir(tmp_path, capsys):
    args = _parser().parse_args(["list", str(tmp_path)])
    rc = run_snapshot_command(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No snapshots" in captured.out
