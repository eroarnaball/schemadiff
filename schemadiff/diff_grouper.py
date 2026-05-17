"""Group diff entries by a chosen dimension (table, severity, change_type)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

GroupBy = Literal["table", "severity", "change_type"]


@dataclass
class GroupedEntry:
    key: str
    tables_added: List[str] = field(default_factory=list)
    tables_removed: List[str] = field(default_factory=list)
    column_changes: List[dict] = field(default_factory=list)

    def total(self) -> int:
        return len(self.tables_added) + len(self.tables_removed) + len(self.column_changes)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "column_changes": self.column_changes,
            "total": self.total(),
        }


@dataclass
class GroupedResult:
    group_by: str
    groups: Dict[str, GroupedEntry] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "group_by": self.group_by,
            "groups": {k: v.to_dict() for k, v in self.groups.items()},
        }


def _severity_for(col_diff) -> str:
    if getattr(col_diff, "old_type", None) != getattr(col_diff, "new_type", None) and \
            getattr(col_diff, "old_type", None) is not None and \
            getattr(col_diff, "new_type", None) is not None:
        return "high"
    if getattr(col_diff, "added", False):
        return "low"
    if getattr(col_diff, "removed", False):
        return "medium"
    return "low"


def _change_type_for(col_diff) -> str:
    if getattr(col_diff, "added", False):
        return "column_added"
    if getattr(col_diff, "removed", False):
        return "column_removed"
    return "column_modified"


def group_result(result, group_by: GroupBy = "table") -> GroupedResult:
    """Group a comparison result by the given dimension."""
    grouped = GroupedResult(group_by=group_by)

    def _get(key: str) -> GroupedEntry:
        if key not in grouped.groups:
            grouped.groups[key] = GroupedEntry(key=key)
        return grouped.groups[key]

    for tname in result.tables_added:
        key = tname if group_by == "table" else ("low" if group_by == "severity" else "table_added")
        _get(key).tables_added.append(tname)

    for tname in result.tables_removed:
        key = tname if group_by == "table" else ("medium" if group_by == "severity" else "table_removed")
        _get(key).tables_removed.append(tname)

    for tname, table_diff in result.column_changes.items():
        for col_diff in table_diff:
            if group_by == "table":
                key = tname
            elif group_by == "severity":
                key = _severity_for(col_diff)
            else:
                key = _change_type_for(col_diff)
            entry = {"table": tname, "column": getattr(col_diff, "column_name", "?")}
            _get(key).column_changes.append(entry)

    return grouped
