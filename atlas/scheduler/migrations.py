"""SQLite schema migrations for the Atlas job scheduler."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Migration:
    """Represents a single schema migration."""

    version: int
    name: str
    sql: str


MIGRATIONS: Iterable[Migration] = (
    Migration(
        version=1,
        name="initial_jobs",
        sql="""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            tenant TEXT NOT NULL,
            payload TEXT NOT NULL,
            schedule_at TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            last_error TEXT,
            retry_policy TEXT NOT NULL,
            runtime_limit REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_schedule
            ON jobs(status, schedule_at);
        CREATE INDEX IF NOT EXISTS idx_jobs_tenant
            ON jobs(tenant, status);
        """,
    ),
)


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def apply_migrations(db_path: Path | str) -> None:
    """Apply all pending migrations to the scheduler database."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        rows = conn.execute(
            "SELECT version FROM scheduler_schema_migrations"
        ).fetchall()
        applied = {row["version"] for row in rows}
        for migration in MIGRATIONS:
            if migration.version in applied:
                continue
            conn.executescript(migration.sql)
            conn.execute(
                """
                INSERT INTO scheduler_schema_migrations (version, name, applied_at)
                VALUES (?, ?, datetime('now'))
                """,
                (migration.version, migration.name),
            )


__all__ = ["apply_migrations", "Migration", "MIGRATIONS"]
