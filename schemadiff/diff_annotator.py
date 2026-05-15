"""Annotate comparison results with human-readable descriptions and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Annotation:
    """A single annotation attached to a diff element."""

    target: str          # e.g. 'table:users' or 'column:users.email'
    kind: str            # 'added' | 'removed' | 'modified'
    message: str
    severity: str = "info"   # 'info' | 'warning' | 'critical'
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "kind": self.kind,
            "message": self.message,
            "severity": self.severity,
            "meta": self.meta,
        }


@dataclass
class AnnotatedResult:
    """Wraps a comparison result with a list of annotations."""

    result: Any
    annotations: List[Annotation] = field(default_factory=list)

    def has_changes(self) -> bool:
        return self.result.has_changes()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.to_dict() if hasattr(self.result, "to_dict") else {},
            "annotations": [a.to_dict() for a in self.annotations],
        }


_SEVERITY_FOR_KIND = {
    "added": "info",
    "removed": "critical",
    "modified": "warning",
}


def annotate_result(result: Any) -> AnnotatedResult:
    """Produce an AnnotatedResult from a ComparisonResult-like object."""
    annotations: List[Annotation] = []

    for table_name in result.tables_added():
        annotations.append(Annotation(
            target=f"table:{table_name}",
            kind="added",
            message=f"Table '{table_name}' was added.",
            severity="info",
        ))

    for table_name in result.tables_removed():
        annotations.append(Annotation(
            target=f"table:{table_name}",
            kind="removed",
            message=f"Table '{table_name}' was removed.",
            severity="critical",
        ))

    for table_name, col_diffs in result.columns_changed().items():
        for col_diff in col_diffs:
            kind = _classify_col_diff(col_diff)
            severity = _SEVERITY_FOR_KIND.get(kind, "info")
            annotations.append(Annotation(
                target=f"column:{table_name}.{col_diff.column_name}",
                kind=kind,
                message=_col_diff_message(table_name, col_diff, kind),
                severity=severity,
                meta={"column": col_diff.column_name},
            ))

    return AnnotatedResult(result=result, annotations=annotations)


def _classify_col_diff(col_diff: Any) -> str:
    if getattr(col_diff, "old", None) is None:
        return "added"
    if getattr(col_diff, "new", None) is None:
        return "removed"
    return "modified"


def _col_diff_message(table: str, col_diff: Any, kind: str) -> str:
    col = col_diff.column_name
    if kind == "added":
        return f"Column '{col}' was added to table '{table}'."
    if kind == "removed":
        return f"Column '{col}' was removed from table '{table}'."
    return f"Column '{col}' in table '{table}' was modified."
