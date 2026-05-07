"""change_log.py – Record and retrieve a chronological log of schema drift events."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


class ChangeLogError(Exception):
    """Raised when the change log cannot be read or written."""


@dataclass
class ChangeLogEntry:
    timestamp: str
    label: str
    total_changes: int
    tables_added: List[str] = field(default_factory=list)
    tables_removed: List[str] = field(default_factory=list)
    tables_modified: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "total_changes": self.total_changes,
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "tables_modified": self.tables_modified,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeLogEntry":
        required = {"timestamp", "label", "total_changes"}
        missing = required - data.keys()
        if missing:
            raise ChangeLogError(f"ChangeLogEntry missing fields: {missing}")
        return cls(
            timestamp=data["timestamp"],
            label=data["label"],
            total_changes=data["total_changes"],
            tables_added=data.get("tables_added", []),
            tables_removed=data.get("tables_removed", []),
            tables_modified=data.get("tables_modified", []),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_entry(log_path: str, entry: ChangeLogEntry) -> None:
    """Append *entry* to the JSON-lines change log at *log_path*."""
    try:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
    except OSError as exc:
        raise ChangeLogError(f"Cannot write change log '{log_path}': {exc}") from exc


def read_entries(log_path: str) -> List[ChangeLogEntry]:
    """Return all entries from the JSON-lines change log at *log_path*."""
    if not os.path.exists(log_path):
        return []
    entries: List[ChangeLogEntry] = []
    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(ChangeLogEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, ChangeLogError) as exc:
                    raise ChangeLogError(f"Bad entry on line {lineno}: {exc}") from exc
    except OSError as exc:
        raise ChangeLogError(f"Cannot read change log '{log_path}': {exc}") from exc
    return entries


def build_entry(label: str, summary) -> ChangeLogEntry:
    """Create a *ChangeLogEntry* from a *SchemaSummary*-like object."""
    d = summary.to_dict() if hasattr(summary, "to_dict") else summary
    return ChangeLogEntry(
        timestamp=_now_iso(),
        label=label,
        total_changes=d.get("total_changes", 0),
        tables_added=d.get("tables_added", []),
        tables_removed=d.get("tables_removed", []),
        tables_modified=d.get("tables_modified", []),
    )
