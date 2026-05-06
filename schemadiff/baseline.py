"""Baseline management: save and load a schema snapshot as a baseline for future comparisons."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from schemadiff.models import Schema
from schemadiff.serializer import schema_to_dict, schema_from_dict


class BaselineError(Exception):
    """Raised when baseline operations fail."""


DEFAULT_BASELINE_FILENAME = ".schemadiff_baseline.json"


def save_baseline(schema: Schema, path: Optional[str] = None) -> Path:
    """Serialize *schema* to JSON and write it to *path*.

    Returns the resolved :class:`Path` that was written.
    """
    target = Path(path or DEFAULT_BASELINE_FILENAME)
    data = schema_to_dict(schema)
    try:
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise BaselineError(f"Could not write baseline to '{target}': {exc}") from exc
    return target


def load_baseline(path: Optional[str] = None) -> Schema:
    """Read a previously saved baseline from *path* and return a :class:`Schema`."""
    source = Path(path or DEFAULT_BASELINE_FILENAME)
    if not source.exists():
        raise BaselineError(
            f"Baseline file '{source}' not found. "
            "Run 'schemadiff baseline save' first."
        )
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline from '{source}': {exc}") from exc
    try:
        return schema_from_dict(raw)
    except Exception as exc:
        raise BaselineError(f"Invalid baseline format in '{source}': {exc}") from exc


def baseline_exists(path: Optional[str] = None) -> bool:
    """Return *True* if a baseline file exists at *path*."""
    return Path(path or DEFAULT_BASELINE_FILENAME).exists()
