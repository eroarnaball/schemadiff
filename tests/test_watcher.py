"""Tests for schemadiff.watcher."""
from __future__ import annotations

import json
import os
import pytest

from schemadiff.watcher import WatcherConfig, WatchError, _single_cycle, watch
from schemadiff.serializer import schema_to_dict
from schemadiff.models import Schema, Table, Column


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_schema(name="db", tables=None):
    return Schema(name=name, tables=tables or {})


def _simple_table(col_name="id", col_type="integer"):
    col = Column(name=col_name, col_type=col_type, nullable=False)
    return Table(name="users", columns={col_name: col})


def _write_json(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# _single_cycle
# ---------------------------------------------------------------------------

def test_single_cycle_no_drift(tmp_path):
    table = _simple_table()
    schema = _make_schema(tables={"users": table})
    payload = schema_to_dict(schema)

    baseline_path = str(tmp_path / "baseline.json")
    live_path = str(tmp_path / "live.json")
    _write_json(baseline_path, payload)
    _write_json(live_path, payload)

    cfg = WatcherConfig(baseline_path=baseline_path, live_schema_path=live_path)
    score = _single_cycle(cfg)
    assert score.score == 0.0
    assert score.severity == "none"


def test_single_cycle_detects_drift(tmp_path):
    table = _simple_table()
    schema_base = _make_schema(tables={"users": table})
    schema_live = _make_schema(tables={})  # table removed

    baseline_path = str(tmp_path / "baseline.json")
    live_path = str(tmp_path / "live.json")
    _write_json(baseline_path, schema_to_dict(schema_base))
    _write_json(live_path, schema_to_dict(schema_live))

    cfg = WatcherConfig(baseline_path=baseline_path, live_schema_path=live_path)
    score = _single_cycle(cfg)
    assert score.score > 0


def test_single_cycle_missing_baseline_raises(tmp_path):
    live_path = str(tmp_path / "live.json")
    _write_json(live_path, schema_to_dict(_make_schema()))

    cfg = WatcherConfig(
        baseline_path=str(tmp_path / "no_such_baseline.json"),
        live_schema_path=live_path,
    )
    with pytest.raises(WatchError, match="baseline"):
        _single_cycle(cfg)


def test_single_cycle_missing_live_raises(tmp_path):
    baseline_path = str(tmp_path / "baseline.json")
    _write_json(baseline_path, schema_to_dict(_make_schema()))

    cfg = WatcherConfig(
        baseline_path=baseline_path,
        live_schema_path=str(tmp_path / "no_such_live.json"),
    )
    with pytest.raises(WatchError, match="live schema"):
        _single_cycle(cfg)


# ---------------------------------------------------------------------------
# watch loop
# ---------------------------------------------------------------------------

def test_watch_calls_on_drift_callback(tmp_path):
    table = _simple_table()
    baseline_path = str(tmp_path / "baseline.json")
    live_path = str(tmp_path / "live.json")
    _write_json(baseline_path, schema_to_dict(_make_schema(tables={"users": table})))
    _write_json(live_path, schema_to_dict(_make_schema(tables={})))

    received = []
    cfg = WatcherConfig(
        baseline_path=baseline_path,
        live_schema_path=live_path,
        interval_seconds=0,
        max_cycles=2,
        on_drift=received.append,
    )
    watch(cfg)
    assert len(received) == 2
    assert all(s.score > 0 for s in received)


def test_watch_no_drift_callback_not_called(tmp_path):
    payload = schema_to_dict(_make_schema())
    baseline_path = str(tmp_path / "baseline.json")
    live_path = str(tmp_path / "live.json")
    _write_json(baseline_path, payload)
    _write_json(live_path, payload)

    received = []
    cfg = WatcherConfig(
        baseline_path=baseline_path,
        live_schema_path=live_path,
        interval_seconds=0,
        max_cycles=3,
        on_drift=received.append,
    )
    watch(cfg)
    assert received == []
