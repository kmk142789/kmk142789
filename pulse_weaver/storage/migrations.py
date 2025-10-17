"""Database migrations for Pulse Weaver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..adapters.base import PulseWeaverAdapter


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
        CREATE TABLE IF NOT EXISTS pulse_weaver_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle TEXT NOT NULL,
            key TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            proof TEXT,
            echo TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_pulse_weaver_events_key
            ON pulse_weaver_events(key);
        CREATE INDEX IF NOT EXISTS idx_pulse_weaver_events_status
            ON pulse_weaver_events(status);

        CREATE TABLE IF NOT EXISTS pulse_weaver_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            atlas_node TEXT,
            phantom_trace TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(key) REFERENCES pulse_weaver_events(key)
        );

        CREATE INDEX IF NOT EXISTS idx_pulse_weaver_links_key
            ON pulse_weaver_links(key);
        """,
    ),
)


def apply_migrations(adapter: PulseWeaverAdapter) -> None:
    with adapter.context() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pulse_weaver_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        rows = conn.execute("SELECT version FROM pulse_weaver_schema_migrations").fetchall()
        applied = {row["version"] for row in rows}
        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            conn.executescript(migration.sql)
            conn.execute(
                """
                INSERT INTO pulse_weaver_schema_migrations (version, name, applied_at)
                VALUES (?, ?, datetime('now'))
                """,
                (migration.version, migration.name),
            )


__all__ = ["apply_migrations", "Migration", "MIGRATIONS"]
