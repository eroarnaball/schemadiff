"""Snapshot management: capture and compare schema snapshots over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from schemadiff.serializer import schema_to_dict, schema_from_dict
from schemadiff.models import Schema


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""


@dataclass
class Snapshot:
    """A timestamped schema snapshot."""

    label: str
    captured_at: str
    schema: Schema
    metadata: Dict[str, str] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def capture_snapshot(schema: Schema, label: str, metadata: Optional[Dict[str, str]] = None) -> Snapshot:
    """Wrap a schema in a Snapshot with the current timestamp."""
    return Snapshot(
        label=label,
        captured_at=_now_iso(),
        schema=schema,
        metadata=metadata or {},
    )


def snapshot_to_dict(snapshot: Snapshot) -> dict:
    return {
        "label": snapshot.label,
        "captured_at": snapshot.captured_at,
        "metadata": snapshot.metadata,
        "schema": schema_to_dict(snapshot.schema),
    }


def snapshot_from_dict(data: dict) -> Snapshot:
    try:
        return Snapshot(
            label=data["label"],
            captured_at=data["captured_at"],
            metadata=data.get("metadata", {}),
            schema=schema_from_dict(data["schema"]),
        )
    except KeyError as exc:
        raise SnapshotError(f"Missing required snapshot field: {exc}") from exc


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot_to_dict(snapshot), fh, indent=2)
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise SnapshotError(f"Snapshot file not found: {path!r}")
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot {path!r}: {exc}") from exc
    return snapshot_from_dict(data)


def list_snapshots(directory: str) -> List[str]:
    """Return sorted list of .json snapshot file paths in a directory."""
    if not os.path.isdir(directory):
        return []
    files = [
        os.path.join(directory, f)
        for f in sorted(os.listdir(directory))
        if f.endswith(".json")
    ]
    return files
