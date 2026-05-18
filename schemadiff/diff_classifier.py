"""Classify diff entries into risk categories based on change characteristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

# Risk levels ordered from lowest to highest
RISK_LEVELS = ("low", "medium", "high", "critical")


@dataclass
class ClassifiedEntry:
    table: str
    change_type: str  # "table_added", "table_removed", "column_added", etc.
    column: str | None
    risk: str  # one of RISK_LEVELS
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table": self.table,
            "change_type": self.change_type,
            "column": self.column,
            "risk": self.risk,
            "reason": self.reason,
        }


@dataclass
class ClassificationResult:
    entries: List[ClassifiedEntry] = field(default_factory=list)

    def by_risk(self, risk: str) -> List[ClassifiedEntry]:
        return [e for e in self.entries if e.risk == risk]

    def highest_risk(self) -> str | None:
        for level in reversed(RISK_LEVELS):
            if self.by_risk(level):
                return level
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highest_risk": self.highest_risk(),
            "total": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


def _classify_column_diff(table: str, col_name: str, col_diff: Any) -> ClassifiedEntry:
    change_type = getattr(col_diff, "change_type", "modified")
    old_type = getattr(col_diff, "old_type", None)
    new_type = getattr(col_diff, "new_type", None)

    if change_type == "removed":
        return ClassifiedEntry(table, "column_removed", col_name, "high",
                               f"Column '{col_name}' removed – may break consumers")
    if change_type == "added":
        nullable = getattr(col_diff, "new_nullable", True)
        risk = "low" if nullable else "medium"
        reason = f"Column '{col_name}' added ({'nullable' if nullable else 'NOT NULL'})"
        return ClassifiedEntry(table, "column_added", col_name, risk, reason)
    # type change
    if old_type and new_type and old_type != new_type:
        return ClassifiedEntry(table, "column_type_changed", col_name, "critical",
                               f"Type changed {old_type} -> {new_type}")
    return ClassifiedEntry(table, "column_modified", col_name, "medium",
                           f"Column '{col_name}' attribute changed")


def classify_result(result: Any) -> ClassificationResult:
    """Walk a comparison/filter result and assign risk to every change."""
    entries: List[ClassifiedEntry] = []

    for tbl in getattr(result, "tables_added", []):
        entries.append(ClassifiedEntry(tbl, "table_added", None, "low",
                                       f"New table '{tbl}' introduced"))
    for tbl in getattr(result, "tables_removed", []):
        entries.append(ClassifiedEntry(tbl, "table_removed", None, "critical",
                                       f"Table '{tbl}' dropped – destructive change"))

    for tbl, table_diff in (getattr(result, "tables_modified", None) or {}).items():
        for col_name, col_diff in (getattr(table_diff, "columns_changed", None) or {}).items():
            entries.append(_classify_column_diff(tbl, col_name, col_diff))

    return ClassificationResult(entries=entries)
