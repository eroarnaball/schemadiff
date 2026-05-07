"""CLI entry-point for the schema drift watcher.

Usage:
    python -m schemadiff.watcher_cli watch \\
        --baseline baseline.json \\
        --live live.json \\
        [--interval 60] \\
        [--cycles 10]
"""
from __future__ import annotations

import argparse
import logging
import sys

from schemadiff.watcher import WatcherConfig, WatchError, watch
from schemadiff.scorer import DriftScore

log = logging.getLogger(__name__)


def _on_drift(score: DriftScore) -> None:
    d = score.to_dict()
    print(
        f"[DRIFT] severity={score.severity}  score={score.score:.2f}  "
        f"tables_added={d['tables_added']}  tables_removed={d['tables_removed']}  "
        f"columns_changed={d['columns_changed']}"
    )


def build_watcher_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemadiff-watch",
        description="Continuously monitor schema drift against a baseline.",
    )
    parser.add_argument("--baseline", required=True, help="Path to baseline JSON file.")
    parser.add_argument("--live", required=True, help="Path to live schema JSON file.")
    parser.add_argument(
        "--interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 60).",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N cycles (default: run forever).",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging."
    )
    return parser


def run_watcher_command(args: argparse.Namespace) -> int:
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")

    config = WatcherConfig(
        baseline_path=args.baseline,
        live_schema_path=args.live,
        interval_seconds=args.interval,
        max_cycles=args.cycles,
        on_drift=_on_drift,
    )
    try:
        watch(config)
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def main(argv=None) -> None:
    parser = build_watcher_parser()
    args = parser.parse_args(argv)
    sys.exit(run_watcher_command(args))


if __name__ == "__main__":  # pragma: no cover
    main()
