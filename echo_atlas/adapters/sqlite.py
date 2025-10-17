"""SQLite storage adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .base import AtlasAdapter


class SQLiteAdapter(AtlasAdapter):
    """SQLite-backed atlas adapter."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


__all__ = ["SQLiteAdapter"]
