"""Tests for schemadiff.classifier_cli."""

from __future__ import annotations

import json
import pathlib
import textwrap

import pytest

from schemadiff.classifier_cli import build_classifier_parser, run_classifier_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_SCHEMA = {
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": True},
            ],
        }
    ]
}

_SCHEMA_TABLE_REMOVED = {
    "tables": []
}

_SCHEMA_COLUMN_ADDED = {
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": True},
                {"name": "phone", "type": "varchar", "nullable": True},
            ],
        }
    ]
}


def _write(tmp_path: pathlib.Path, name: str, payload: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(payload))
    return str(p)


def _parser():
    return build_classifier_parser()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_changes_exits_zero(tmp_path):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _BASE_SCHEMA)
    args = _parser().parse_args([old, new])
    assert run_classifier_command(args) == 0


def test_column_added_exits_zero_no_fail_on(tmp_path):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _SCHEMA_COLUMN_ADDED)
    args = _parser().parse_args([old, new])
    assert run_classifier_command(args) == 0


def test_table_removed_fail_on_critical(tmp_path):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _SCHEMA_TABLE_REMOVED)
    args = _parser().parse_args([old, new, "--fail-on", "critical"])
    assert run_classifier_command(args) == 1


def test_table_removed_fail_on_low(tmp_path):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _SCHEMA_TABLE_REMOVED)
    args = _parser().parse_args([old, new, "--fail-on", "low"])
    assert run_classifier_command(args) == 1


def test_json_format_output(tmp_path, capsys):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _SCHEMA_TABLE_REMOVED)
    args = _parser().parse_args([old, new, "--format", "json"])
    run_classifier_command(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert data["highest_risk"] == "critical"


def test_min_risk_filters_output(tmp_path, capsys):
    old = _write(tmp_path, "old.json", _BASE_SCHEMA)
    new = _write(tmp_path, "new.json", _SCHEMA_COLUMN_ADDED)
    args = _parser().parse_args([old, new, "--min-risk", "critical", "--format", "json"])
    run_classifier_command(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 0


def test_missing_file_returns_exit_code_2(tmp_path):
    args = _parser().parse_args(["nonexistent_old.json", "nonexistent_new.json"])
    assert run_classifier_command(args) == 2
