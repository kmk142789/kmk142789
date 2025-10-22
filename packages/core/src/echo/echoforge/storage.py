"""SQLite-backed session storage for the EchoForge dashboard."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Mapping


@dataclass(slots=True)
class StoredSession:
    """Persistent session metadata."""

    session_id: str
    created_at: datetime
    client_host: str | None
    client_port: int | None
    user_agent: str | None
    pulse_count: int

    def as_dict(self) -> Mapping[str, object | None]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "client_host": self.client_host,
            "client_port": self.client_port,
            "user_agent": self.user_agent,
            "pulse_count": self.pulse_count,
        }


class EchoForgeSessionStore:
    """Persist websocket sessions and their associated pulse events."""

    def __init__(self, database_path: Path) -> None:
        self._db_path = Path(database_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        session_id: str,
        client_host: str | None,
        client_port: int | None,
        user_agent: str | None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, created_at, client_host, client_port, user_agent)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    client_host=excluded.client_host,
                    client_port=excluded.client_port,
                    user_agent=excluded.user_agent
                """,
                (
                    session_id,
                    datetime.now(timezone.utc).isoformat(),
                    client_host,
                    client_port,
                    user_agent,
                ),
            )

    def store_pulse(
        self,
        session_id: str,
        *,
        event_payload: Mapping[str, object],
    ) -> None:
        pulse = dict(event_payload)
        pulse_json = json.dumps(pulse, ensure_ascii=False)
        attestation = event_payload.get("attestation")
        atlas = event_payload.get("atlas")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO pulses (session_id, captured_at, payload, attestation, atlas)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    datetime.now(timezone.utc).isoformat(),
                    pulse_json,
                    json.dumps(attestation, ensure_ascii=False) if attestation is not None else None,
                    json.dumps(atlas, ensure_ascii=False) if atlas is not None else None,
                ),
            )

    def sessions(self, *, limit: int = 50) -> list[StoredSession]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT s.id, s.created_at, s.client_host, s.client_port, s.user_agent, COUNT(p.id) as pulse_count
                FROM sessions AS s
                LEFT JOIN pulses AS p ON p.session_id = s.id
                GROUP BY s.id
                ORDER BY s.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        result: list[StoredSession] = []
        for row in rows:
            created = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            result.append(
                StoredSession(
                    session_id=row["id"],
                    created_at=created,
                    client_host=row["client_host"],
                    client_port=row["client_port"],
                    user_agent=row["user_agent"],
                    pulse_count=int(row["pulse_count"] or 0),
                )
            )
        return result

    def session_payload(self, session_id: str, *, limit: int = 500) -> Mapping[str, object]:
        with self._connection() as conn:
            session_row = conn.execute(
                "SELECT id, created_at, client_host, client_port, user_agent FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            pulse_rows = conn.execute(
                """
                SELECT id, captured_at, payload, attestation, atlas
                FROM pulses
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        if not session_row:
            raise KeyError(f"unknown session '{session_id}'")
        created = (
            datetime.fromisoformat(session_row["created_at"]) if session_row["created_at"] else datetime.now(timezone.utc)
        )
        pulses = [
            {
                "id": row["id"],
                "captured_at": row["captured_at"],
                "payload": json.loads(row["payload"]),
                "attestation": json.loads(row["attestation"]) if row["attestation"] else None,
                "atlas": json.loads(row["atlas"]) if row["atlas"] else None,
            }
            for row in pulse_rows
        ]
        return {
            "session": {
                "session_id": session_row["id"],
                "created_at": created.isoformat(),
                "client_host": session_row["client_host"],
                "client_port": session_row["client_port"],
                "user_agent": session_row["user_agent"],
                "pulse_count": len(pulses),
            },
            "pulses": pulses,
        }

    def recent_pulses(self, *, limit: int = 50) -> list[Mapping[str, object]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT session_id, captured_at, payload
                FROM pulses
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        entries = []
        for row in rows:
            payload = json.loads(row["payload"])
            payload["session_id"] = row["session_id"]
            payload["captured_at"] = row["captured_at"]
            entries.append(payload)
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    client_host TEXT,
                    client_port INTEGER,
                    user_agent TEXT
                );
                CREATE TABLE IF NOT EXISTS pulses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    captured_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    attestation TEXT,
                    atlas TEXT
                );
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()


__all__ = ["EchoForgeSessionStore", "StoredSession"]
