"""CLI entry-point for the diff annotator."""

from __future__ import annotations

import argparse
import json
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.diff_annotator import annotate_result


def build_annotator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="schemadiff-annotate",
        description="Annotate schema diff with human-readable messages.",
    )
    p.add_argument("old", help="Path to the old schema JSON file.")
    p.add_argument("new", help="Path to the new schema JSON file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--min-severity",
        choices=["info", "warning", "critical"],
        default="info",
        dest="min_severity",
        help="Only show annotations at or above this severity.",
    )
    return p


_SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


def run_annotator_command(args: argparse.Namespace, out=sys.stdout) -> int:
    try:
        old_schema = load_schema_from_file(args.old)
        new_schema = load_schema_from_file(args.new)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading schemas: {exc}", file=sys.stderr)
        return 1

    result = compare_schemas(old_schema, new_schema)
    annotated = annotate_result(result)

    min_level = _SEVERITY_ORDER.get(args.min_severity, 0)
    visible = [
        a for a in annotated.annotations
        if _SEVERITY_ORDER.get(a.severity, 0) >= min_level
    ]

    if args.format == "json":
        payload = {
            "has_changes": annotated.has_changes(),
            "annotations": [a.to_dict() for a in visible],
        }
        print(json.dumps(payload, indent=2), file=out)
    else:
        if not visible:
            print("No annotations to display.", file=out)
        else:
            for ann in visible:
                print(f"[{ann.severity.upper()}] {ann.target}: {ann.message}", file=out)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_annotator_parser()
    sys.exit(run_annotator_command(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
