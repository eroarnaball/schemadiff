"""Human-readable text reporter for SchemaDiff results."""

from schemadiff.differ import ColumnDiff, SchemaDiff, TableDiff


CHANGE_SYMBOLS = {
    "added": "+",
    "removed": "-",
    "modified": "~",
}


def _format_column_diff(diff: ColumnDiff) -> str:
    symbol = CHANGE_SYMBOLS.get(diff.change, "?")
    if diff.change == "added":
        col = diff.new_value
        return (
            f"    {symbol} COLUMN {diff.column!r}: "
            f"{col.data_type} nullable={col.nullable} default={col.default!r}"
        )
    elif diff.change == "removed":
        col = diff.old_value
        return (
            f"    {symbol} COLUMN {diff.column!r}: "
            f"{col.data_type} nullable={col.nullable} default={col.default!r}"
        )
    else:  # modified
        old, new = diff.old_value, diff.new_value
        changes = []
        if old.data_type != new.data_type:
            changes.append(f"type: {old.data_type!r} -> {new.data_type!r}")
        if old.nullable != new.nullable:
            changes.append(f"nullable: {old.nullable} -> {new.nullable}")
        if old.default != new.default:
            changes.append(f"default: {old.default!r} -> {new.default!r}")
        if old.primary_key != new.primary_key:
            changes.append(f"primary_key: {old.primary_key} -> {new.primary_key}")
        return f"    {symbol} COLUMN {diff.column!r}: " + ", ".join(changes)


def _format_table_diff(diff: TableDiff) -> str:
    symbol = CHANGE_SYMBOLS.get(diff.change, "?")
    lines = [f"  {symbol} TABLE {diff.table!r}"]
    for col_diff in diff.column_diffs:
        lines.append(_format_column_diff(col_diff))
    return "\n".join(lines)


def format_diff(diff: SchemaDiff) -> str:
    """Return a formatted string report of a SchemaDiff."""
    header = f"Schema Diff: {diff.source_name!r} -> {diff.target_name!r}"
    separator = "=" * len(header)
    lines = [header, separator]

    if not diff.has_changes:
        lines.append("  No changes detected.")
    else:
        for table_diff in diff.table_diffs:
            lines.append(_format_table_diff(table_diff))

    return "\n".join(lines)


def print_diff(diff: SchemaDiff) -> None:
    """Print the formatted diff to stdout."""
    print(format_diff(diff))
