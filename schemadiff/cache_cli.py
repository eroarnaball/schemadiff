"""CLI sub-commands for managing the diff cache."""

from __future__ import annotations

import argparse
import sys

from schemadiff.diff_cache import CacheError, clear_cache, get_cached, put_cached


def build_cache_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Manage the schemadiff diff cache."
    if parent is not None:
        parser = parent.add_parser("cache", help=description)
    else:
        parser = argparse.ArgumentParser(prog="schemadiff-cache", description=description)

    sub = parser.add_subparsers(dest="cache_cmd", required=True)

    clear_p = sub.add_parser("clear", help="Remove all cached diff results.")
    clear_p.add_argument("--cache-dir", default=".schemadiff_cache", metavar="DIR")

    stats_p = sub.add_parser("stats", help="Show cache directory stats.")
    stats_p.add_argument("--cache-dir", default=".schemadiff_cache", metavar="DIR")

    return parser


def _cmd_clear(args: argparse.Namespace) -> int:
    try:
        removed = clear_cache(args.cache_dir)
    except CacheError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Removed {removed} cache entry/entries from '{args.cache_dir}'.")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    from pathlib import Path

    directory = Path(args.cache_dir)
    if not directory.exists():
        print(f"Cache directory '{args.cache_dir}' does not exist.")
        return 0
    entries = list(directory.glob("*.json"))
    total_bytes = sum(e.stat().st_size for e in entries)
    print(f"Cache directory : {args.cache_dir}")
    print(f"Entries         : {len(entries)}")
    print(f"Total size      : {total_bytes} bytes")
    return 0


def run_cache_command(args: argparse.Namespace) -> int:
    dispatch = {"clear": _cmd_clear, "stats": _cmd_stats}
    handler = dispatch.get(args.cache_cmd)
    if handler is None:
        print(f"Unknown cache sub-command: {args.cache_cmd}", file=sys.stderr)
        return 1
    return handler(args)


def main() -> None:  # pragma: no cover
    parser = build_cache_parser()
    args = parser.parse_args()
    sys.exit(run_cache_command(args))


if __name__ == "__main__":  # pragma: no cover
    main()
