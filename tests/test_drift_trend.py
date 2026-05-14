"""Tests for schemadiff.drift_trend and schemadiff.trend_cli."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from schemadiff.drift_trend import DriftTrend, TrendPoint, build_trend


# ---------------------------------------------------------------------------
# TrendPoint
# ---------------------------------------------------------------------------

def test_trend_point_to_dict():
    p = TrendPoint(label="v1", score=3.5, severity="low")
    assert p.to_dict() == {"label": "v1", "score": 3.5, "severity": "low"}


def test_trend_point_from_dict_roundtrip():
    d = {"label": "v2", "score": 7.0, "severity": "high"}
    p = TrendPoint.from_dict(d)
    assert p.label == "v2"
    assert p.score == 7.0
    assert p.severity == "high"


def test_trend_point_from_dict_missing_field_raises():
    with pytest.raises(ValueError, match="missing fields"):
        TrendPoint.from_dict({"label": "v1", "score": 1.0})


# ---------------------------------------------------------------------------
# DriftTrend
# ---------------------------------------------------------------------------

def _trend(*scores) -> DriftTrend:
    t = DriftTrend()
    for i, s in enumerate(scores):
        t = t.add(TrendPoint(label=f"v{i}", score=s, severity="low"))
    return t


def test_direction_stable_single_point():
    assert _trend(5.0).direction() == "stable"


def test_direction_stable_equal_scores():
    assert _trend(3.0, 3.0, 3.0).direction() == "stable"


def test_direction_worsening():
    assert _trend(1.0, 3.0, 6.0).direction() == "worsening"


def test_direction_improving():
    assert _trend(8.0, 4.0, 1.0).direction() == "improving"


def test_average_score_empty():
    assert DriftTrend().average_score() == 0.0


def test_average_score_values():
    assert _trend(2.0, 4.0, 6.0).average_score() == pytest.approx(4.0)


def test_to_dict_keys():
    d = _trend(1.0, 2.0).to_dict()
    assert set(d.keys()) == {"points", "direction", "average_score"}
    assert len(d["points"]) == 2


# ---------------------------------------------------------------------------
# build_trend
# ---------------------------------------------------------------------------

def test_build_trend_from_list():
    data = [
        {"label": "a", "score": 1.0, "severity": "low"},
        {"label": "b", "score": 5.0, "severity": "medium"},
    ]
    trend = build_trend(data)
    assert trend.direction() == "worsening"
    assert len(trend.points) == 2


# ---------------------------------------------------------------------------
# trend_cli
# ---------------------------------------------------------------------------

def _write_history(tmp_path: Path, data) -> Path:
    p = tmp_path / "history.json"
    p.write_text(json.dumps(data))
    return p


def test_trend_cli_text_output(tmp_path, capsys):
    from schemadiff.trend_cli import build_trend_parser, run_trend_command

    history = _write_history(tmp_path, [
        {"label": "v1", "score": 2.0, "severity": "low"},
        {"label": "v2", "score": 4.0, "severity": "medium"},
    ])
    parser = build_trend_parser()
    args = parser.parse_args([str(history)])
    rc = run_trend_command(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "worsening" in out
    assert "v1" in out


def test_trend_cli_json_output(tmp_path, capsys):
    from schemadiff.trend_cli import build_trend_parser, run_trend_command

    history = _write_history(tmp_path, [
        {"label": "x", "score": 3.0, "severity": "low"},
    ])
    parser = build_trend_parser()
    args = parser.parse_args([str(history), "--format", "json"])
    rc = run_trend_command(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "direction" in payload
    assert "average_score" in payload


def test_trend_cli_missing_file(tmp_path, capsys):
    from schemadiff.trend_cli import build_trend_parser, run_trend_command

    parser = build_trend_parser()
    args = parser.parse_args([str(tmp_path / "nope.json")])
    rc = run_trend_command(args)
    assert rc == 2


def test_trend_cli_invalid_json(tmp_path):
    from schemadiff.trend_cli import build_trend_parser, run_trend_command

    p = tmp_path / "bad.json"
    p.write_text("not json")
    parser = build_trend_parser()
    args = parser.parse_args([str(p)])
    assert run_trend_command(args) == 2


def test_trend_cli_not_a_list(tmp_path):
    from schemadiff.trend_cli import build_trend_parser, run_trend_command

    p = _write_history(tmp_path, {"wrong": "type"})
    parser = build_trend_parser()
    args = parser.parse_args([str(p)])
    assert run_trend_command(args) == 2
