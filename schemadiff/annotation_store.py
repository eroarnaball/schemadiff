"""Persist and retrieve AnnotatedResult annotations to/from JSON files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from schemadiff.diff_annotator import Annotation


class AnnotationStoreError(Exception):
    """Raised when the store cannot read or write annotations."""


def save_annotations(annotations: List[Annotation], path: str | os.PathLike) -> None:
    """Serialise *annotations* to a JSON file at *path*."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = [a.to_dict() for a in annotations]
    try:
        dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise AnnotationStoreError(f"Cannot write annotations to {path}: {exc}") from exc


def load_annotations(path: str | os.PathLike) -> List[Annotation]:
    """Load annotations previously saved with :func:`save_annotations`."""
    src = Path(path)
    if not src.exists():
        raise AnnotationStoreError(f"Annotation file not found: {path}")
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnnotationStoreError(f"Cannot read annotations from {path}: {exc}") from exc

    if not isinstance(raw, list):
        raise AnnotationStoreError("Annotation file must contain a JSON array.")

    return [_annotation_from_dict(item) for item in raw]


def _annotation_from_dict(d: Dict[str, Any]) -> Annotation:
    required = ("target", "kind", "message")
    for key in required:
        if key not in d:
            raise AnnotationStoreError(f"Annotation entry missing required field: '{key}'")
    return Annotation(
        target=d["target"],
        kind=d["kind"],
        message=d["message"],
        severity=d.get("severity", "info"),
        meta=d.get("meta", {}),
    )


def list_annotation_files(directory: str | os.PathLike) -> List[Path]:
    """Return all .json files in *directory* sorted by name."""
    d = Path(directory)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.json"))
