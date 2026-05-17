"""CLI entry-point for sorted diff output."""

from __future__ import annotations

import argparse
import json
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.diff_sorter import SortConfig, sort_result


def build_sorter_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="schemadiff-sort",
        description="Compare two schemas and emit changes in sorted order.",
    )
    p.add_argument("before", help="Path to the 'before' schema JSON file.")
    p.add_argument("after", help="Path to the 'after' schema JSON file.")
    p.add_argument(
        "--key",
        choices=["severity", "table_name", "change_type", "column_count"],
        default="severity",
        help="Primary sort key (default: severity).",
    )
    p.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="asc",
        help="Sort order (default: asc).",
    )
    p.add_argument(
        "--secondary-key",
        choices=["severity", "table_name", "change_type", "column_count"],
        default="table_name",
        dest="secondary_key",
        help="Secondary sort key (default: table_name).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return p


def run_sorter_command(args: argparse.Namespace) -> int:
    try:
        before = load_schema_from_file(args.before)
        after = load_schema_from_file(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(before, after)
    config = SortConfig(key=args.key, order=args.order, secondary_key=args.secondary_key)
    entries = sort_result(result, config)

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        if not entries:
            print("No schema changes detected.")
        else:
            for e in entries:
                col_part = f" / {e.column_name}" if e.column_name else ""
                detail_part = f" ({e.detail})" if e.detail else ""
                print(f"[{e.change_type}] {e.table_name}{col_part}{detail_part}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_sorter_parser()
    sys.exit(run_sorter_command(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
