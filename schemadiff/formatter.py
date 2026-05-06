"""Formatter for SchemaSummary — renders summary as text or dict."""

from schemadiff.summary import SchemaSummary


def format_summary_text(summary: SchemaSummary) -> str:
    """Return a human-readable text block for a SchemaSummary."""
    lines = [
        "=== Schema Diff Summary ===",
        f"  Tables added    : {summary.tables_added}",
        f"  Tables removed  : {summary.tables_removed}",
        f"  Tables modified : {summary.tables_modified}",
        f"  Tables unchanged: {summary.tables_unchanged}",
        "",
        f"  Columns added   : {summary.columns_added}",
        f"  Columns removed : {summary.columns_removed}",
        f"  Columns modified: {summary.columns_modified}",
        "",
        f"  Total changes   : {summary.total_changes}",
    ]
    if not summary.has_changes:
        lines.append("  (no changes detected)")
    return "\n".join(lines)


def format_summary_markdown(summary: SchemaSummary) -> str:
    """Return a Markdown table representation of the summary."""
    rows = [
        ("Tables Added", summary.tables_added),
        ("Tables Removed", summary.tables_removed),
        ("Tables Modified", summary.tables_modified),
        ("Tables Unchanged", summary.tables_unchanged),
        ("Columns Added", summary.columns_added),
        ("Columns Removed", summary.columns_removed),
        ("Columns Modified", summary.columns_modified),
        ("**Total Changes**", summary.total_changes),
    ]
    lines = [
        "## Schema Diff Summary",
        "",
        "| Metric | Count |",
        "|--------|------|",
    ]
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def format_summary(summary: SchemaSummary, fmt: str = "text") -> str:
    """Dispatch to the appropriate formatter.

    Args:
        summary: A SchemaSummary instance.
        fmt: One of 'text' or 'markdown'.

    Returns:
        Formatted string.

    Raises:
        ValueError: If fmt is not recognised.
    """
    if fmt == "text":
        return format_summary_text(summary)
    if fmt == "markdown":
        return format_summary_markdown(summary)
    raise ValueError(f"Unknown summary format: {fmt!r}. Choose 'text' or 'markdown'.")
