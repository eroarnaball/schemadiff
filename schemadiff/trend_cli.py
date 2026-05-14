"""CLI entry point for drift trend analysis."""

from __future__ import annotations

import argparse
import json
import sys

from schemadiff.drift_trend import build_trend


def build_trend_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Analyse drift score trend from a JSON history file."
    if parent is not None:
        parser = parent.add_parser("trend", help=description)
    else:
        parser = argparse.ArgumentParser(prog="schemadiff-trend", description=description)
    parser.add_argument("history", help="Path to JSON file containing list of scored snapshots")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def run_trend_command(args: argparse.Namespace) -> int:
    try:
        with open(args.history, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"error: file not found: {args.history}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, list):
        print("error: history file must contain a JSON array", file=sys.stderr)
        return 2

    try:
        trend = build_trend(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(trend.to_dict(), indent=2))
    else:
        d = trend.to_dict()
        print(f"Direction   : {d['direction']}")
        print(f"Avg score   : {d['average_score']}")
        print(f"Data points : {len(d['points'])}")
        for p in d["points"]:
            print(f"  [{p['label']}] score={p['score']}  severity={p['severity']}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_trend_parser()
    args = parser.parse_args()
    sys.exit(run_trend_command(args))


if __name__ == "__main__":  # pragma: no cover
    main()
