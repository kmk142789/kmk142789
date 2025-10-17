"""Database migrations for Echo Atlas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..adapters.base import AtlasAdapter


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


MIGRATIONS: Iterable[Migration] = (
    Migration(
        version=1,
        name="initial",
        sql="""
        CREATE TABLE IF NOT EXISTS atlas_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS atlas_nodes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS atlas_edges (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            relation TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(source) REFERENCES atlas_nodes(id),
            FOREIGN KEY(target) REFERENCES atlas_nodes(id)
        );

        CREATE TABLE IF NOT EXISTS atlas_change_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            change_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT NOT NULL,
            payload TEXT
        );

        CREATE TABLE IF NOT EXISTS atlas_highlights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            content TEXT NOT NULL
        );
        """,
    ),
)


def apply_migrations(adapter: AtlasAdapter) -> None:
    with adapter.context() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS atlas_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        rows = conn.execute("SELECT version FROM atlas_schema_migrations").fetchall()
        applied = {row["version"] for row in rows}
        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            conn.executescript(migration.sql)
            conn.execute(
                """
                INSERT INTO atlas_schema_migrations (version, name, applied_at)
                VALUES (?, ?, datetime('now'))
                """,
                (migration.version, migration.name),
            )
