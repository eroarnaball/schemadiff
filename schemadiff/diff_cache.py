"""Simple file-backed cache for comparison results to avoid redundant diffs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional


class CacheError(Exception):
    """Raised when the diff cache encounters an unrecoverable problem."""


def _content_hash(text: str) -> str:
    """Return a short SHA-256 hex digest for *text*."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _cache_key(schema_a_text: str, schema_b_text: str) -> str:
    """Derive a deterministic cache key from two raw schema strings."""
    combined = _content_hash(schema_a_text) + "-" + _content_hash(schema_b_text)
    return combined


def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def get_cached(
    cache_dir: str | Path,
    schema_a_text: str,
    schema_b_text: str,
) -> Optional[dict]:
    """Return cached result dict if present, else *None*."""
    path = _cache_path(Path(cache_dir), _cache_key(schema_a_text, schema_b_text))
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise CacheError(f"Failed to read cache entry {path}: {exc}") from exc


def put_cached(
    cache_dir: str | Path,
    schema_a_text: str,
    schema_b_text: str,
    result: dict,
) -> Path:
    """Persist *result* to the cache and return the file path written."""
    directory = Path(cache_dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CacheError(f"Cannot create cache directory {directory}: {exc}") from exc
    path = _cache_path(directory, _cache_key(schema_a_text, schema_b_text))
    try:
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    except OSError as exc:
        raise CacheError(f"Failed to write cache entry {path}: {exc}") from exc
    return path


def invalidate(
    cache_dir: str | Path,
    schema_a_text: str,
    schema_b_text: str,
) -> bool:
    """Delete a cache entry.  Returns *True* if a file was removed."""
    path = _cache_path(Path(cache_dir), _cache_key(schema_a_text, schema_b_text))
    if path.exists():
        path.unlink()
        return True
    return False


def clear_cache(cache_dir: str | Path) -> int:
    """Remove all cache entries.  Returns the count of deleted files."""
    directory = Path(cache_dir)
    if not directory.exists():
        return 0
    removed = 0
    for entry in directory.glob("*.json"):
        entry.unlink()
        removed += 1
    return removed
