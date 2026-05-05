"""Core data models for representing database schema objects."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Column:
    """Represents a single column in a database table."""
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return NotImplemented
        return (
            self.name == other.name
            and self.data_type == other.data_type
            and self.nullable == other.nullable
            and self.default == other.default
            and self.primary_key == other.primary_key
        )

    def __repr__(self) -> str:
        return (
            f"Column(name={self.name!r}, data_type={self.data_type!r}, "
            f"nullable={self.nullable}, default={self.default!r}, "
            f"primary_key={self.primary_key})"
        )


@dataclass
class Table:
    """Represents a database table with its columns."""
    name: str
    columns: list[Column] = field(default_factory=list)

    def get_column(self, name: str) -> Optional[Column]:
        """Return a column by name, or None if not found."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    @property
    def column_names(self) -> set[str]:
        return {col.name for col in self.columns}

    def __repr__(self) -> str:
        return f"Table(name={self.name!r}, columns={self.columns!r})"


@dataclass
class Schema:
    """Represents a full database schema containing multiple tables."""
    name: str
    tables: list[Table] = field(default_factory=list)

    def get_table(self, name: str) -> Optional[Table]:
        """Return a table by name, or None if not found."""
        for table in self.tables:
            if table.name == name:
                return table
        return None

    @property
    def table_names(self) -> set[str]:
        return {table.name for table in self.tables}

    def __repr__(self) -> str:
        return f"Schema(name={self.name!r}, tables={self.tables!r})"
