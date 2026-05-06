"""Tests for schemadiff.baseline."""

from __future__ import annotations

import json
import pytest

from schemadiff.models import Column, Table, Schema
from schemadiff.baseline import (
    save_baseline,
    load_baseline,
    baseline_exists,
    BaselineError,
    DEFAULT_BASELINE_FILENAME,
)


def _make_schema() -> Schema:
    col_id = Column(name="id", col_type="INTEGER", nullable=False)
    col_name = Column(name="name", col_type="TEXT", nullable=True)
    table = Table(name="users", columns=[col_id, col_name])
    return Schema(tables=[table])


def test_save_baseline_creates_file(tmp_path):
    schema = _make_schema()
    target = tmp_path / "baseline.json"
    result = save_baseline(schema, str(target))
    assert result == target
    assert target.exists()


def test_save_baseline_valid_json(tmp_path):
    schema = _make_schema()
    target = tmp_path / "baseline.json"
    save_baseline(schema, str(target))
    data = json.loads(target.read_text())
    assert "tables" in data


def test_load_baseline_roundtrip(tmp_path):
    schema = _make_schema()
    target = tmp_path / "baseline.json"
    save_baseline(schema, str(target))
    loaded = load_baseline(str(target))
    assert len(loaded.tables) == 1
    assert loaded.tables[0].name == "users"
    assert len(loaded.tables[0].columns) == 2


def test_load_baseline_missing_file(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline(str(tmp_path / "nonexistent.json"))


def test_load_baseline_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("NOT JSON", encoding="utf-8")
    with pytest.raises(BaselineError):
        load_baseline(str(bad))


def test_baseline_exists_true(tmp_path):
    schema = _make_schema()
    target = tmp_path / "bl.json"
    save_baseline(schema, str(target))
    assert baseline_exists(str(target)) is True


def test_baseline_exists_false(tmp_path):
    assert baseline_exists(str(tmp_path / "missing.json")) is False


def test_save_baseline_default_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    schema = _make_schema()
    result = save_baseline(schema)
    assert result.name == DEFAULT_BASELINE_FILENAME
    assert result.exists()


def test_save_baseline_bad_path():
    with pytest.raises(BaselineError, match="Could not write"):
        save_baseline(_make_schema(), "/nonexistent_dir/baseline.json")
