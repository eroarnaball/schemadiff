"""Persist and retrieve ClassificationResult objects as JSON files."""

from __future__ import annotations

import json
import pathlib
from typing import List

from schemadiff.diff_classifier import ClassifiedEntry, ClassificationResult


class ClassifierStoreError(Exception):
    """Raised when a store operation fails."""


def save_classification(result: ClassificationResult, path: str | pathlib.Path) -> None:
    """Serialise *result* to *path* as JSON."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(json.dumps(result.to_dict(), indent=2))
    except OSError as exc:
        raise ClassifierStoreError(f"Cannot write classification to {p}: {exc}") from exc


def load_classification(path: str | pathlib.Path) -> ClassificationResult:
    """Load a previously saved ClassificationResult from *path*."""
    p = pathlib.Path(path)
    if not p.exists():
        raise ClassifierStoreError(f"Classification file not found: {p}")
    try:
        raw = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ClassifierStoreError(f"Cannot read classification from {p}: {exc}") from exc

    entries: List[ClassifiedEntry] = []
    for item in raw.get("entries", []):
        entries.append(
            ClassifiedEntry(
                table=item["table"],
                change_type=item["change_type"],
                column=item.get("column"),
                risk=item["risk"],
                reason=item["reason"],
            )
        )
    return ClassificationResult(entries=entries)


def list_classification_files(directory: str | pathlib.Path) -> List[pathlib.Path]:
    """Return all ``*.json`` files inside *directory*, sorted by name."""
    d = pathlib.Path(directory)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.json"))
