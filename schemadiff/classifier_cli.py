"""CLI entry-point for the diff classifier."""

from __future__ import annotations

import argparse
import json
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.diff_classifier import classify_result, RISK_LEVELS


def build_classifier_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        description="Classify schema drift entries by risk level."
    )
    if parent is not None:
        parser = parent.add_parser("classify", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument("old", help="Path to the old schema JSON file")
    parser.add_argument("new", help="Path to the new schema JSON file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--min-risk",
        choices=RISK_LEVELS,
        default="low",
        help="Only show entries at or above this risk level (default: low)",
    )
    parser.add_argument(
        "--fail-on",
        choices=RISK_LEVELS,
        default=None,
        help="Exit with code 1 if any entry meets or exceeds this risk level",
    )
    return parser


def run_classifier_command(args: argparse.Namespace) -> int:
    try:
        old_schema = load_schema_from_file(args.old)
        new_schema = load_schema_from_file(args.new)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(old_schema, new_schema)
    classification = classify_result(result)

    min_idx = RISK_LEVELS.index(args.min_risk)
    visible = [e for e in classification.entries if RISK_LEVELS.index(e.risk) >= min_idx]

    if args.format == "json":
        payload = {
            "highest_risk": classification.highest_risk(),
            "total": len(visible),
            "entries": [e.to_dict() for e in visible],
        }
        print(json.dumps(payload, indent=2))
    else:
        if not visible:
            print("No classification entries above minimum risk.")
        else:
            for e in visible:
                col_part = f"  column={e.column}" if e.column else ""
                print(f"[{e.risk.upper()}] {e.table}{col_part}: {e.reason}")

    if args.fail_on:
        fail_idx = RISK_LEVELS.index(args.fail_on)
        if any(RISK_LEVELS.index(e.risk) >= fail_idx for e in classification.entries):
            return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_classifier_parser()
    args = parser.parse_args()
    sys.exit(run_classifier_command(args))


if __name__ == "__main__":  # pragma: no cover
    main()
