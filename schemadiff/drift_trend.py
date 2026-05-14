"""Drift trend analysis: track DriftScore history and compute trend direction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

TrendDirection = Literal["improving", "stable", "worsening"]


@dataclass
class TrendPoint:
    label: str
    score: float
    severity: str

    def to_dict(self) -> dict:
        return {"label": self.label, "score": self.score, "severity": self.severity}

    @staticmethod
    def from_dict(d: dict) -> "TrendPoint":
        missing = [k for k in ("label", "score", "severity") if k not in d]
        if missing:
            raise ValueError(f"TrendPoint missing fields: {missing}")
        return TrendPoint(label=d["label"], score=float(d["score"]), severity=d["severity"])


@dataclass
class DriftTrend:
    points: List[TrendPoint] = field(default_factory=list)

    def add(self, point: TrendPoint) -> "DriftTrend":
        return DriftTrend(points=self.points + [point])

    def direction(self) -> TrendDirection:
        if len(self.points) < 2:
            return "stable"
        first = self.points[0].score
        last = self.points[-1].score
        delta = last - first
        if delta > 0:
            return "worsening"
        if delta < 0:
            return "improving"
        return "stable"

    def average_score(self) -> float:
        if not self.points:
            return 0.0
        return sum(p.score for p in self.points) / len(self.points)

    def to_dict(self) -> dict:
        return {
            "points": [p.to_dict() for p in self.points],
            "direction": self.direction(),
            "average_score": round(self.average_score(), 4),
        }


def build_trend(scored_snapshots: List[dict]) -> DriftTrend:
    """Build a DriftTrend from a list of {label, score, severity} dicts."""
    trend = DriftTrend()
    for entry in scored_snapshots:
        trend = trend.add(TrendPoint.from_dict(entry))
    return trend
