"""SQLite adapter for Pulse Weaver."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .base import PulseWeaverAdapter


class SQLiteAdapter(PulseWeaverAdapter):
    """SQLite-backed adapter that stores ledger information on disk."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


__all__ = ["SQLiteAdapter"]
