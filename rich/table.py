"""Lightweight stand-in for ``rich.table.Table`` used in tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class Table:
    """Extremely small subset of the real Rich ``Table`` API."""

    title: str | None = None
    columns: List[dict[str, str | None]] = field(default_factory=list)
    rows: List[Sequence[str]] = field(default_factory=list)

    def add_column(self, header: str, *, justify: str | None = None) -> None:
        self.columns.append({"header": header, "justify": justify})

    def add_row(self, *values: object) -> None:
        self.rows.append(tuple(str(value) for value in values))
