"""Sort and prioritize diff results by various criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

SortKey = Literal["severity", "table_name", "change_type", "column_count"]
SortOrder = Literal["asc", "desc"]

_CHANGE_TYPE_RANK = {
    "table_removed": 0,
    "table_added": 1,
    "column_removed": 2,
    "type_changed": 3,
    "nullable_changed": 4,
    "column_added": 5,
}


@dataclass
class SortConfig:
    key: SortKey = "severity"
    order: SortOrder = "asc"
    secondary_key: Optional[SortKey] = "table_name"


@dataclass
class SortedEntry:
    table_name: str
    change_type: str
    column_name: Optional[str] = None
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "table_name": self.table_name,
            "change_type": self.change_type,
            "column_name": self.column_name,
            "detail": self.detail,
        }


def _severity_rank(entry: SortedEntry) -> int:
    return _CHANGE_TYPE_RANK.get(entry.change_type, 99)


def _sort_key_fn(key: SortKey):
    if key == "severity":
        return _severity_rank
    if key == "table_name":
        return lambda e: e.table_name.lower()
    if key == "change_type":
        return lambda e: e.change_type
    if key == "column_count":
        return lambda e: 0 if e.column_name is None else 1
    return lambda e: 0


def _collect_entries(result) -> List[SortedEntry]:
    entries: List[SortedEntry] = []
    for t in result.tables_added:
        entries.append(SortedEntry(table_name=t, change_type="table_added"))
    for t in result.tables_removed:
        entries.append(SortedEntry(table_name=t, change_type="table_removed"))
    for t_name, t_diff in result.tables_modified.items():
        for col in t_diff.columns_added:
            entries.append(SortedEntry(t_name, "column_added", col))
        for col in t_diff.columns_removed:
            entries.append(SortedEntry(t_name, "column_removed", col))
        for col, cd in t_diff.columns_modified.items():
            if cd.old_type != cd.new_type:
                entries.append(SortedEntry(t_name, "type_changed", col,
                                           f"{cd.old_type} -> {cd.new_type}"))
            elif cd.old_nullable != cd.new_nullable:
                entries.append(SortedEntry(t_name, "nullable_changed", col,
                                           f"{cd.old_nullable} -> {cd.new_nullable}"))
    return entries


def sort_result(result, config: Optional[SortConfig] = None) -> List[SortedEntry]:
    """Return a sorted flat list of SortedEntry objects from a comparison result."""
    if config is None:
        config = SortConfig()
    entries = _collect_entries(result)
    reverse = config.order == "desc"
    primary_fn = _sort_key_fn(config.key)
    if config.secondary_key and config.secondary_key != config.key:
        secondary_fn = _sort_key_fn(config.secondary_key)
        entries.sort(key=lambda e: (primary_fn(e), secondary_fn(e)), reverse=reverse)
    else:
        entries.sort(key=primary_fn, reverse=reverse)
    return entries
