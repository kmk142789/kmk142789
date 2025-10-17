"""Migration primitives for the Echo Atlas schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List

from ..adapters.base import StorageAdapter


@dataclass(frozen=True)
class Migration:
    """Single migration step consisting of SQL statements."""

    version: int
    statements: Iterable[str]
    description: str


MIGRATIONS: List[Migration] = [
    Migration(
        version=1,
        description="Initial atlas tables",
        statements=[
            """
            CREATE TABLE IF NOT EXISTS atlas_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
        ],
    ),
]


def apply_migrations(adapter: StorageAdapter) -> None:
    """Apply pending migrations using the supplied adapter connection."""

    connection = getattr(adapter, "connection", None)
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute("SELECT COALESCE(MAX(version), 0) FROM migrations")
    current = cursor.fetchone()[0] or 0

    for migration in MIGRATIONS:
        if migration.version <= current:
            continue
        for statement in migration.statements:
            cursor.execute(statement)
        cursor.execute(
            "INSERT INTO migrations(version, applied_at) VALUES(?, ?)",
            (migration.version, datetime.now(tz=timezone.utc).isoformat()),
        )
    connection.commit()
