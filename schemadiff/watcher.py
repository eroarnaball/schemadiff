"""Periodic schema drift watcher: compares a live schema against a baseline
and emits a DriftScore each polling cycle."""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from schemadiff.baseline import load_baseline, BaselineError
from schemadiff.loader import load_schema_from_file, LoadError
from schemadiff.comparator import compare_schemas
from schemadiff.scorer import score_result, DriftScore

log = logging.getLogger(__name__)


@dataclass
class WatcherConfig:
    """Configuration for a SchemaWatcher instance."""
    baseline_path: str
    live_schema_path: str
    interval_seconds: float = 60.0
    max_cycles: Optional[int] = None  # None = run forever
    on_drift: Callable[[DriftScore], None] = field(
        default_factory=lambda: lambda score: None
    )


class WatchError(Exception):
    """Raised when the watcher cannot complete a cycle."""


def _single_cycle(config: WatcherConfig) -> DriftScore:
    """Load schemas, compare, and return a DriftScore for one cycle."""
    try:
        baseline_schema = load_baseline(config.baseline_path)
    except (BaselineError, FileNotFoundError) as exc:
        raise WatchError(f"Cannot load baseline '{config.baseline_path}': {exc}") from exc

    try:
        live_schema = load_schema_from_file(config.live_schema_path)
    except (LoadError, FileNotFoundError) as exc:
        raise WatchError(f"Cannot load live schema '{config.live_schema_path}': {exc}") from exc

    result = compare_schemas(baseline_schema, live_schema)
    return score_result(result)


def watch(config: WatcherConfig) -> None:
    """Run the watcher loop.  Blocks until *max_cycles* is reached."""
    cycle = 0
    while config.max_cycles is None or cycle < config.max_cycles:
        try:
            score = _single_cycle(config)
            log.info(
                "[cycle %d] severity=%s total_changes=%d score=%.2f",
                cycle,
                score.severity,
                score.to_dict()["total_changes"],
                score.score,
            )
            if score.score > 0:
                config.on_drift(score)
        except WatchError as exc:
            log.error("[cycle %d] watch error: %s", cycle, exc)

        cycle += 1
        if config.max_cycles is None or cycle < config.max_cycles:
            time.sleep(config.interval_seconds)
