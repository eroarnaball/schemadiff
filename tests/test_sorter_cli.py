"""Tests for schemadiff.sorter_cli."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from schemadiff.sorter_cli import build_sorter_parser, run_sorter_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCHEMA_A = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": True},
            ],
        }
    ]
})

_SCHEMA_B = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "bigint", "nullable": False},
            ],
        },
        {
            "name": "orders",
            "columns": [
                {"name": "order_id", "type": "int", "nullable": False},
            ],
        },
    ]
})


def _write_schema(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


def _parser():
    return build_sorter_parser()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_changes_exits_zero(tmp_path):
    p = _write_schema(_SCHEMA_A)
    args = _parser().parse_args([p, p])
    assert run_sorter_command(args) == 0


def test_no_changes_text_says_no_changes(capsys, tmp_path):
    p = _write_schema(_SCHEMA_A)
    args = _parser().parse_args([p, p])
    run_sorter_command(args)
    out = capsys.readouterr().out
    assert "No schema changes" in out


def test_changes_text_output(capsys):
    before = _write_schema(_SCHEMA_A)
    after = _write_schema(_SCHEMA_B)
    args = _parser().parse_args([before, after])
    rc = run_sorter_command(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "orders" in out


def test_json_format_output(capsys):
    before = _write_schema(_SCHEMA_A)
    after = _write_schema(_SCHEMA_B)
    args = _parser().parse_args([before, after, "--format", "json"])
    run_sorter_command(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("change_type" in item for item in data)


def test_sort_by_table_name(capsys):
    before = _write_schema(_SCHEMA_A)
    after = _write_schema(_SCHEMA_B)
    args = _parser().parse_args([before, after, "--key", "table_name", "--format", "json"])
    run_sorter_command(args)
    data = json.loads(capsys.readouterr().out)
    names = [d["table_name"] for d in data]
    assert names == sorted(names, key=str.lower)


def test_missing_file_returns_error_code(capsys):
    args = _parser().parse_args(["/nonexistent/a.json", "/nonexistent/b.json"])
    rc = run_sorter_command(args)
    assert rc == 2
