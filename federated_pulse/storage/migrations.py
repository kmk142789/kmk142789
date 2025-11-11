"""Schema migrations for the Federated Pulse SQLite store."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


MIGRATIONS: Iterable[Migration] = (
    Migration(
        version=1,
        name="initial_lww",
        sql="""
        CREATE TABLE IF NOT EXISTS lww (
            k TEXT PRIMARY KEY,
            v BLOB,
            ts INTEGER,
            node TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_lww_timestamp
            ON lww(ts, node);
        """,
    ),
)


def apply_migrations(db_path: Path | str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fpulse_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {
            row[0]
            for row in conn.execute(
                "SELECT version FROM fpulse_schema_migrations"
            ).fetchall()
        }
        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            conn.executescript(migration.sql)
            conn.execute(
                """
                INSERT INTO fpulse_schema_migrations (version, name, applied_at)
                VALUES (?, ?, datetime('now'))
                """,
                (migration.version, migration.name),
            )


__all__ = ["apply_migrations", "Migration", "MIGRATIONS"]
