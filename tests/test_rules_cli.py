"""Integration tests for schemadiff.rules_cli."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from schemadiff.rules_cli import build_rules_parser, run_rules_command


_SCHEMA_NO_CHANGES = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "email", "type": "text", "nullable": False},
            ],
        }
    ]
})

_SCHEMA_TYPE_CHANGED = json.dumps({
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "email", "type": "varchar", "nullable": False},  # type changed
            ],
        }
    ]
})

_SCHEMA_TABLE_REMOVED = json.dumps({
    "tables": []
})


def _write(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.fixture()
def parser():
    return build_rules_parser()


def test_no_violations_exit_zero(parser, tmp_path):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_NO_CHANGES)
    args = parser.parse_args([old, new])
    assert run_rules_command(args) == 0


def test_type_change_violation_no_fail_flag(parser, capsys):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_TYPE_CHANGED)
    args = parser.parse_args([old, new])
    code = run_rules_command(args)
    assert code == 0  # no --fail-on-violation
    captured = capsys.readouterr()
    assert "no_type_change" in captured.out


def test_type_change_violation_with_fail_flag(parser):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_TYPE_CHANGED)
    args = parser.parse_args([old, new, "--fail-on-violation"])
    assert run_rules_command(args) == 1


def test_table_removed_violation(parser, capsys):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_TABLE_REMOVED)
    args = parser.parse_args([old, new, "--fail-on-violation"])
    code = run_rules_command(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "no_table_removed" in captured.out


def test_json_output_structure(parser, capsys):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_TYPE_CHANGED)
    args = parser.parse_args([old, new, "--format", "json"])
    run_rules_command(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "violations" in data
    assert "total" in data
    assert "has_violations" in data


def test_rule_filter_limits_output(parser, capsys):
    old = _write(_SCHEMA_NO_CHANGES)
    new = _write(_SCHEMA_TABLE_REMOVED)
    # Only ask for no_column_removed; table removal should not appear
    args = parser.parse_args([old, new, "--rules", "no_column_removed"])
    run_rules_command(args)
    captured = capsys.readouterr()
    assert "no_table_removed" not in captured.out


def test_missing_file_returns_exit_code_2(parser):
    args = parser.parse_args(["/nonexistent/old.json", "/nonexistent/new.json"])
    assert run_rules_command(args) == 2
