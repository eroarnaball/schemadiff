"""Schema diff engine: compares two Schema objects and produces a SchemaDiff report."""

from dataclasses import dataclass, field
from typing import Optional

from schemadiff.models import Column, Schema, Table


@dataclass
class ColumnDiff:
    table: str
    column: str
    change: str  # 'added', 'removed', 'modified'
    old_value: Optional[Column] = None
    new_value: Optional[Column] = None


@dataclass
class TableDiff:
    table: str
    change: str  # 'added', 'removed', 'modified'
    column_diffs: list[ColumnDiff] = field(default_factory=list)


@dataclass
class SchemaDiff:
    source_name: str
    target_name: str
    table_diffs: list[TableDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.table_diffs) > 0

    @property
    def summary(self) -> str:
        """Return a short human-readable summary of the diff."""
        added = sum(1 for t in self.table_diffs if t.change == "added")
        removed = sum(1 for t in self.table_diffs if t.change == "removed")
        modified = sum(1 for t in self.table_diffs if t.change == "modified")
        return (
            f"{self.source_name} -> {self.target_name}: "
            f"{added} table(s) added, {removed} removed, {modified} modified"
        )

    def get_table_diff(self, table_name: str) -> Optional["TableDiff"]:
        """Return the TableDiff for a specific table, or None if not found."""
        for td in self.table_diffs:
            if td.table == table_name:
                return td
        return None


def _diff_columns(table_name: str, source: Table, target: Table) -> list[ColumnDiff]:
    diffs: list[ColumnDiff] = []
    added = target.column_names - source.column_names
    removed = source.column_names - target.column_names
    common = source.column_names & target.column_names

    for col_name in sorted(added):
        diffs.append(ColumnDiff(
            table=table_name, column=col_name, change="added",
            new_value=target.get_column(col_name)
        ))
    for col_name in sorted(removed):
        diffs.append(ColumnDiff(
            table=table_name, column=col_name, change="removed",
            old_value=source.get_column(col_name)
        ))
    for col_name in sorted(common):
        src_col = source.get_column(col_name)
        tgt_col = target.get_column(col_name)
        if src_col != tgt_col:
            diffs.append(ColumnDiff(
                table=table_name, column=col_name, change="modified",
                old_value=src_col, new_value=tgt_col
            ))
    return diffs


def diff_schemas(source: Schema, target: Schema) -> SchemaDiff:
    """Compare two schemas and return a SchemaDiff describing all changes."""
    result = SchemaDiff(source_name=source.name, target_name=target.name)

    added_tables = target.table_names - source.table_names
    removed_tables = source.table_names - target.table_names
    common_tables = source.table_names & target.table_names

    for t in sorted(added_tables):
        result.table_diffs.append(TableDiff(table=t, change="added"))
    for t in sorted(removed_tables):
        result.table_diffs.append(TableDiff(table=t, change="removed"))
    for t in sorted(common_tables):
        col_diffs = _diff_columns(t,
            source.get_table(t), target.get_table(t))
        if col_diffs:
            result.table_diffs.append(TableDiff(table=t, change="modified", column_diffs=col_diffs))

    return result
