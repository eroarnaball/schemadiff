"""Tests for schemadiff.baseline_cli."""

from __future__ import annotations

import json
import argparse
import pytest

from schemadiff.baseline_cli import build_baseline_parser, run_baseline_command


def _schema_payload(table_name: str = "orders") -> dict:
    return {
        "tables": [
            {
                "name": table_name,
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "total", "type": "FLOAT", "nullable": True},
                ],
            }
        ]
    }


def _write_schema(tmp_path, payload, filename="schema.json"):
    p = tmp_path / filename
    p.write_text(json.dumps(payload), encoding="utf-8")
    return str(p)


def _parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_baseline_parser(sub)
    return p


def test_save_creates_baseline(tmp_path):
    schema_path = _write_schema(tmp_path, _schema_payload())
    baseline_path = str(tmp_path / "bl.json")
    parser = _parser()
    args = parser.parse_args(["baseline", "save", schema_path, "--output", baseline_path])
    code = run_baseline_command(args)
    assert code == 0
    assert (tmp_path / "bl.json").exists()


def test_compare_no_changes_exit_zero(tmp_path):
    schema_path = _write_schema(tmp_path, _schema_payload())
    baseline_path = str(tmp_path / "bl.json")
    parser = _parser()
    # save
    args = parser.parse_args(["baseline", "save", schema_path, "--output", baseline_path])
    run_baseline_command(args)
    # compare — same schema
    args2 = parser.parse_args(
        ["baseline", "compare", schema_path, "--baseline", baseline_path, "--exit-code"]
    )
    code = run_baseline_command(args2)
    assert code == 0


def test_compare_with_drift_exit_one(tmp_path):
    old_path = _write_schema(tmp_path, _schema_payload(), "old.json")
    new_payload = _schema_payload()
    new_payload["tables"][0]["columns"].append({"name": "discount", "type": "FLOAT", "nullable": True})
    new_path = _write_schema(tmp_path, new_payload, "new.json")
    baseline_path = str(tmp_path / "bl.json")
    parser = _parser()
    args = parser.parse_args(["baseline", "save", old_path, "--output", baseline_path])
    run_baseline_command(args)
    args2 = parser.parse_args(
        ["baseline", "compare", new_path, "--baseline", baseline_path, "--exit-code"]
    )
    code = run_baseline_command(args2)
    assert code == 1


def test_save_bad_schema_path(tmp_path):
    parser = _parser()
    args = parser.parse_args(["baseline", "save", "/no/such/file.json"])
    code = run_baseline_command(args)
    assert code == 2


def test_compare_missing_baseline(tmp_path):
    schema_path = _write_schema(tmp_path, _schema_payload())
    parser = _parser()
    args = parser.parse_args(
        ["baseline", "compare", schema_path, "--baseline", str(tmp_path / "missing.json")]
    )
    code = run_baseline_command(args)
    assert code == 2
