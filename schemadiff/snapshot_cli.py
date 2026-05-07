"""CLI commands for schema snapshot capture and diff."""

from __future__ import annotations

import argparse
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.snapshotter import (
    capture_snapshot,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    SnapshotError,
)
from schemadiff.comparator import compare_schemas
from schemadiff.exporter import export_to_json, export_to_markdown


def build_snapshot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemadiff-snapshot",
        description="Capture and compare schema snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_capture = sub.add_parser("capture", help="Capture a snapshot from a schema file.")
    p_capture.add_argument("schema_file", help="Path to schema JSON file.")
    p_capture.add_argument("output", help="Path to write the snapshot JSON.")
    p_capture.add_argument("--label", default="snapshot", help="Human-readable label.")

    p_diff = sub.add_parser("diff", help="Diff two snapshot files.")
    p_diff.add_argument("before", help="Path to the 'before' snapshot JSON.")
    p_diff.add_argument("after", help="Path to the 'after' snapshot JSON.")
    p_diff.add_argument("--format", choices=["text", "json", "markdown"], default="text")

    p_list = sub.add_parser("list", help="List snapshots in a directory.")
    p_list.add_argument("directory", help="Directory containing snapshot files.")

    return parser


def _cmd_capture(args: argparse.Namespace) -> int:
    try:
        schema = load_schema_from_file(args.schema_file)
        snapshot = capture_snapshot(schema, label=args.label)
        save_snapshot(snapshot, args.output)
        print(f"Snapshot '{args.label}' saved to {args.output}")
        return 0
    except (SnapshotError, Exception) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _cmd_diff(args: argparse.Namespace) -> int:
    try:
        before = load_snapshot(args.before)
        after = load_snapshot(args.after)
    except SnapshotError as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    result = compare_schemas(before.schema, after.schema)

    if args.format == "json":
        print(export_to_json(result))
    elif args.format == "markdown":
        print(export_to_markdown(result))
    else:
        from schemadiff.reporter import format_diff
        print(format_diff(result))

    return 1 if result.has_changes() else 0


def _cmd_list(args: argparse.Namespace) -> int:
    paths = list_snapshots(args.directory)
    if not paths:
        print(f"No snapshots found in {args.directory!r}")
        return 0
    for p in paths:
        print(p)
    return 0


def run_snapshot_command(args: argparse.Namespace) -> int:
    dispatch = {"capture": _cmd_capture, "diff": _cmd_diff, "list": _cmd_list}
    return dispatch[args.command](args)


def main() -> None:
    parser = build_snapshot_parser()
    args = parser.parse_args()
    sys.exit(run_snapshot_command(args))


if __name__ == "__main__":
    main()
