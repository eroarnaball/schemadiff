"""Tests for schemadiff.annotator_cli."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from schemadiff.annotator_cli import build_annotator_parser, run_annotator_command


_OLD_SCHEMA = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": False},
            ],
        }
    ]
})

_NEW_SCHEMA_COL_ADDED = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": False},
                {"name": "phone", "type": "varchar", "nullable": True},
            ],
        }
    ]
})

_NEW_SCHEMA_TABLE_REMOVED = json.dumps({"tables": []})


def _write_schema(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, content.encode())
    os.close(fd)
    return path


def _parser():
    return build_annotator_parser()


def test_no_changes_exits_zero(capsys):
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_OLD_SCHEMA)
    args = _parser().parse_args([old, new])
    rc = run_annotator_command(args)
    assert rc == 0


def test_no_changes_text_says_no_annotations(capsys):
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_OLD_SCHEMA)
    args = _parser().parse_args([old, new])
    import io
    out = io.StringIO()
    run_annotator_command(args, out=out)
    assert "No annotations" in out.getvalue()


def test_column_added_text_output(capsys):
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_NEW_SCHEMA_COL_ADDED)
    import io
    out = io.StringIO()
    args = _parser().parse_args([old, new])
    run_annotator_command(args, out=out)
    text = out.getvalue()
    assert "phone" in text
    assert "INFO" in text


def test_table_removed_text_shows_critical(capsys):
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_NEW_SCHEMA_TABLE_REMOVED)
    import io
    out = io.StringIO()
    args = _parser().parse_args([old, new])
    run_annotator_command(args, out=out)
    assert "CRITICAL" in out.getvalue()


def test_json_format_output():
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_NEW_SCHEMA_COL_ADDED)
    import io
    out = io.StringIO()
    args = _parser().parse_args([old, new, "--format", "json"])
    run_annotator_command(args, out=out)
    data = json.loads(out.getvalue())
    assert "annotations" in data
    assert "has_changes" in data
    assert data["has_changes"] is True


def test_min_severity_filters_info():
    old = _write_schema(_OLD_SCHEMA)
    new = _write_schema(_NEW_SCHEMA_COL_ADDED)
    import io
    out = io.StringIO()
    args = _parser().parse_args([old, new, "--min-severity", "warning"])
    run_annotator_command(args, out=out)
    # column added is 'info', should be filtered out
    assert "phone" not in out.getvalue()


def test_bad_file_returns_error_code():
    args = _parser().parse_args(["/nonexistent_old.json", "/nonexistent_new.json"])
    rc = run_annotator_command(args)
    assert rc == 1
