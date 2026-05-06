"""Utility helpers for managing multiple named baselines in a directory store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from schemadiff.models import Schema
from schemadiff.serializer import schema_to_dict, schema_from_dict
from schemadiff.baseline import BaselineError


DEFAULT_STORE_DIR = ".schemadiff"


class BaselineStore:
    """A directory-backed store of named schema baselines."""

    def __init__(self, store_dir: Optional[str] = None) -> None:
        self._dir = Path(store_dir or DEFAULT_STORE_DIR)

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        return self._dir / f"{name}.json"

    def save(self, name: str, schema: Schema) -> Path:
        """Persist *schema* under *name*. Returns the file path."""
        self._ensure_dir()
        target = self._path_for(name)
        try:
            target.write_text(json.dumps(schema_to_dict(schema), indent=2), encoding="utf-8")
        except OSError as exc:
            raise BaselineError(f"Cannot save baseline '{name}': {exc}") from exc
        return target

    def load(self, name: str) -> Schema:
        """Load and return the baseline stored under *name*."""
        source = self._path_for(name)
        if not source.exists():
            raise BaselineError(
                f"No baseline named '{name}' in store '{self._dir}'."
            )
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
            return schema_from_dict(raw)
        except (OSError, json.JSONDecodeError, Exception) as exc:
            raise BaselineError(f"Cannot load baseline '{name}': {exc}") from exc

    def delete(self, name: str) -> None:
        """Remove the baseline stored under *name*."""
        target = self._path_for(name)
        if not target.exists():
            raise BaselineError(f"No baseline named '{name}' to delete.")
        target.unlink()

    def list_baselines(self) -> List[str]:
        """Return sorted list of stored baseline names."""
        if not self._dir.exists():
            return []
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def exists(self, name: str) -> bool:
        """Return *True* if a baseline with *name* exists."""
        return self._path_for(name).exists()
