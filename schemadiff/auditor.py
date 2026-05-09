"""Audit log for schema comparison events.

Records who compared what schemas and when, producing a structured
audit trail that can be persisted or forwarded to external systems.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditError(Exception):
    """Raised when an audit operation fails."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


@dataclass
class AuditEntry:
    event: str
    source_label: str
    target_label: str
    timestamp: str = field(default_factory=_now_iso)
    hostname: str = field(default_factory=_hostname)
    total_changes: int = 0
    tables_added: int = 0
    tables_removed: int = 0
    columns_modified: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "source_label": self.source_label,
            "target_label": self.target_label,
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "total_changes": self.total_changes,
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "columns_modified": self.columns_modified,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AuditEntry":
        required = {
            "event", "source_label", "target_label",
            "timestamp", "hostname",
        }
        missing = required - data.keys()
        if missing:
            raise AuditError(f"AuditEntry missing fields: {sorted(missing)}")
        return AuditEntry(
            event=data["event"],
            source_label=data["source_label"],
            target_label=data["target_label"],
            timestamp=data["timestamp"],
            hostname=data["hostname"],
            total_changes=data.get("total_changes", 0),
            tables_added=data.get("tables_added", 0),
            tables_removed=data.get("tables_removed", 0),
            columns_modified=data.get("columns_modified", 0),
            metadata=data.get("metadata", {}),
        )


def record_comparison(
    result,
    source_label: str,
    target_label: str,
    log_path: Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Append a comparison audit entry to *log_path* (newline-delimited JSON)."""
    ta = len(result.tables_added)
    tr = len(result.tables_removed)
    cm = sum(
        1
        for td in result.tables_modified.values()
        for _ in (td.columns_added + td.columns_removed + list(td.columns_modified.values()))
    ) if hasattr(result, "tables_modified") else 0

    entry = AuditEntry(
        event="schema_comparison",
        source_label=source_label,
        target_label=target_label,
        total_changes=ta + tr + cm,
        tables_added=ta,
        tables_removed=tr,
        columns_modified=cm,
        metadata=metadata or {},
    )
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log: {exc}") from exc
    return entry


def load_audit_log(log_path: Path) -> List[AuditEntry]:
    """Read all audit entries from a newline-delimited JSON file."""
    if not log_path.exists():
        return []
    entries: List[AuditEntry] = []
    with log_path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditError(f"Invalid JSON on line {lineno}: {exc}") from exc
            entries.append(AuditEntry.from_dict(data))
    return entries
