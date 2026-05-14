"""Tests for schemadiff.cache_cli."""

from __future__ import annotations

import argparse
import pytest

from schemadiff.cache_cli import build_cache_parser, run_cache_command
from schemadiff.diff_cache import put_cached

RESULT = {"has_changes": False}
SCHEMA_A = '{"tables": []}'
SCHEMA_B = '{"tables": [{"name": "t"}]}'


def _parser() -> argparse.ArgumentParser:
    return build_cache_parser()


def test_clear_empty_dir_exits_zero(tmp_path):
    parser = _parser()
    args = parser.parse_args(["clear", "--cache-dir", str(tmp_path)])
    assert run_cache_command(args) == 0


def test_clear_removes_entries(tmp_path):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    parser = _parser()
    args = parser.parse_args(["clear", "--cache-dir", str(tmp_path)])
    code = run_cache_command(args)
    assert code == 0
    remaining = list(tmp_path.glob("*.json"))
    assert remaining == []


def test_clear_output_mentions_count(tmp_path, capsys):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    parser = _parser()
    args = parser.parse_args(["clear", "--cache-dir", str(tmp_path)])
    run_cache_command(args)
    out = capsys.readouterr().out
    assert "1" in out


def test_stats_nonexistent_dir_exits_zero(tmp_path):
    missing = tmp_path / "no_such_dir"
    parser = _parser()
    args = parser.parse_args(["stats", "--cache-dir", str(missing)])
    assert run_cache_command(args) == 0


def test_stats_shows_entry_count(tmp_path, capsys):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    parser = _parser()
    args = parser.parse_args(["stats", "--cache-dir", str(tmp_path)])
    run_cache_command(args)
    out = capsys.readouterr().out
    assert "1" in out


def test_stats_shows_directory_path(tmp_path, capsys):
    parser = _parser()
    args = parser.parse_args(["stats", "--cache-dir", str(tmp_path)])
    run_cache_command(args)
    out = capsys.readouterr().out
    assert str(tmp_path) in out


def test_unknown_subcommand_returns_one(tmp_path):
    ns = argparse.Namespace(cache_cmd="bogus", cache_dir=str(tmp_path))
    assert run_cache_command(ns) == 1
