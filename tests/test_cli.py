"""Tests for schemadiff.cli."""

import json
import os
import tempfile

import pytest

from schemadiff.cli import run


def _write_schema(data: dict) -> str:
    """Write a schema dict to a temp JSON file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    return path


SIMPLE_SCHEMA = {
    "tables": {
        "users": {
            "columns": {
                "id": {"type": "int", "nullable": False},
                "name": {"type": "varchar(100)", "nullable": True},
            }
        }
    }
}

MODIFIED_SCHEMA = {
    "tables": {
        "users": {
            "columns": {
                "id": {"type": "int", "nullable": False},
                "name": {"type": "varchar(255)", "nullable": True},
                "email": {"type": "text", "nullable": True},
            }
        },
        "orders": {
            "columns": {
                "id": {"type": "int", "nullable": False},
            }
        },
    }
}


def test_cli_no_changes_exit_zero():
    path = _write_schema(SIMPLE_SCHEMA)
    try:
        code = run([path, path, "--exit-code"])
        assert code == 0
    finally:
        os.unlink(path)


def test_cli_changes_exit_one_with_flag():
    old = _write_schema(SIMPLE_SCHEMA)
    new = _write_schema(MODIFIED_SCHEMA)
    try:
        code = run([old, new, "--exit-code"])
        assert code == 1
    finally:
        os.unlink(old)
        os.unlink(new)


def test_cli_changes_exit_zero_without_flag():
    old = _write_schema(SIMPLE_SCHEMA)
    new = _write_schema(MODIFIED_SCHEMA)
    try:
        code = run([old, new])
        assert code == 0
    finally:
        os.unlink(old)
        os.unlink(new)


def test_cli_json_format_output(capsys):
    old = _write_schema(SIMPLE_SCHEMA)
    new = _write_schema(MODIFIED_SCHEMA)
    try:
        run([old, new, "--format", "json"])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert "has_changes" in payload
        assert payload["has_changes"] is True
    finally:
        os.unlink(old)
        os.unlink(new)


def test_cli_markdown_format_output(capsys):
    old = _write_schema(SIMPLE_SCHEMA)
    new = _write_schema(MODIFIED_SCHEMA)
    try:
        run([old, new, "--format", "markdown"])
        captured = capsys.readouterr()
        assert "# Schema Diff Report" in captured.out
    finally:
        os.unlink(old)
        os.unlink(new)


def test_cli_csv_format_output(capsys):
    old = _write_schema(SIMPLE_SCHEMA)
    new = _write_schema(MODIFIED_SCHEMA)
    try:
        run([old, new, "--format", "csv"])
        captured = capsys.readouterr()
        assert "change_type" in captured.out
    finally:
        os.unlink(old)
        os.unlink(new)


def test_cli_missing_file_returns_2():
    code = run(["nonexistent_old.json", "nonexistent_new.json"])
    assert code == 2
