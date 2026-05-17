"""CLI sub-command: merge two or more schema diff results."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemadiff.diff_merger import merge_results, MergeError
from schemadiff.loader import load_schema_from_file, LoadError
from schemadiff.comparator import compare_schemas


def build_merger_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Merge drift results from multiple schema comparisons."
    if parent is not None:
        parser = parent.add_parser("merge", help=description)
    else:
        parser = argparse.ArgumentParser(prog="schemadiff-merge", description=description)

    parser.add_argument("pairs", nargs="+", metavar="OLD:NEW",
                        help="Colon-separated pairs of schema files to compare (e.g. old.json:new.json).")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text).")
    parser.add_argument("--fail-on-changes", action="store_true",
                        help="Exit with code 1 when any drift is detected.")
    return parser


def run_merger_command(args: argparse.Namespace) -> int:
    results = []
    labels = []

    for pair in args.pairs:
        if ":" not in pair:
            print(f"ERROR: Invalid pair '{pair}'. Expected OLD:NEW format.", file=sys.stderr)
            return 2
        old_path, new_path = pair.split(":", 1)
        try:
            old_schema = load_schema_from_file(old_path)
            new_schema = load_schema_from_file(new_path)
        except LoadError as exc:
            print(f"ERROR loading schemas for '{pair}': {exc}", file=sys.stderr)
            return 2

        results.append(compare_schemas(old_schema, new_schema))
        labels.append(f"{Path(old_path).name}→{Path(new_path).name}")

    try:
        merged = merge_results(results, labels=labels)
    except MergeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(merged.to_dict(), indent=2))
    else:
        if not merged.has_changes():
            print("No schema drift detected across all comparisons.")
        else:
            if merged.tables_added:
                print("Tables added:", ", ".join(merged.tables_added))
            if merged.tables_removed:
                print("Tables removed:", ", ".join(merged.tables_removed))
            if merged.column_changes:
                print(f"Column changes: {len(merged.column_changes)} total")

    return 1 if (args.fail_on_changes and merged.has_changes()) else 0


def main() -> None:  # pragma: no cover
    parser = build_merger_parser()
    args = parser.parse_args()
    sys.exit(run_merger_command(args))
