"""SQLite persistence layer for the Echo Vault."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .crypto import generate_salt
from .models import VaultPolicy, VaultRecord

__all__ = ["VaultStore"]


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value BLOB
);

CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    fmt TEXT NOT NULL,
    tags TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_used_at REAL,
    use_count INTEGER NOT NULL,
    entropy_hint TEXT NOT NULL,
    policy TEXT NOT NULL,
    enc_priv BLOB NOT NULL,
    nonce BLOB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_records_label ON records(label);
CREATE INDEX IF NOT EXISTS idx_records_tags ON records(tags);
CREATE INDEX IF NOT EXISTS idx_records_created ON records(created_at);
"""


class VaultStore:
    """Persistence abstraction that wraps a SQLite database."""

    VERSION = "1"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            if self._read_meta("version") is None:
                self._write_meta("version", self.VERSION)
            if self._read_meta("salt") is None:
                self._write_meta("salt", generate_salt())
            self._conn.commit()

    # ------------------------------------------------------------------
    # Meta helpers
    # ------------------------------------------------------------------
    def _write_meta(self, key: str, value: bytes | str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value)
            )

    def _read_meta(self, key: str) -> Optional[bytes]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return None if row is None else row[0]

    def salt(self) -> bytes:
        value = self._read_meta("salt")
        if value is None:
            raise RuntimeError("vault salt is missing")
        return value

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def insert_record(
        self,
        record: VaultRecord,
        *,
        enc_priv: bytes,
        nonce: bytes,
    ) -> None:
        payload = (
            record.id,
            record.label,
            record.fmt,
            json.dumps(record.tags, separators=(",", ":")),
            record.created_at,
            record.last_used_at,
            record.use_count,
            record.entropy_hint,
            record.policy.model_dump_json(),
            enc_priv,
            nonce,
        )
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO records(
                    id, label, fmt, tags, created_at, last_used_at,
                    use_count, entropy_hint, policy, enc_priv, nonce
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            self._conn.commit()

    def list_records(self) -> List[VaultRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, label, fmt, tags, created_at, last_used_at, use_count, entropy_hint, policy FROM records"
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def fetch_record(self, record_id: str) -> Tuple[VaultRecord, bytes, bytes]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM records WHERE id=?", (record_id,)
            ).fetchone()
        if row is None:
            raise KeyError(record_id)
        record = self._row_to_record(row)
        return record, row["enc_priv"], row["nonce"]

    def update_usage(
        self,
        record_id: str,
        *,
        use_count: int,
        last_used_at: float,
        entropy_hint: Optional[str] = None,
    ) -> VaultRecord:
        with self._lock:
            if entropy_hint is not None:
                self._conn.execute(
                    "UPDATE records SET use_count=?, last_used_at=?, entropy_hint=? WHERE id=?",
                    (use_count, last_used_at, entropy_hint, record_id),
                )
            else:
                self._conn.execute(
                    "UPDATE records SET use_count=?, last_used_at=? WHERE id=?",
                    (use_count, last_used_at, record_id),
                )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT id, label, fmt, tags, created_at, last_used_at, use_count, entropy_hint, policy FROM records WHERE id=?",
                (record_id,),
            ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return self._row_to_record(row)

    def update_policy(self, record_id: str, policy: VaultPolicy) -> VaultRecord:
        with self._lock:
            self._conn.execute(
                "UPDATE records SET policy=? WHERE id=?",
                (policy.model_dump_json(), record_id),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT id, label, fmt, tags, created_at, last_used_at, use_count, entropy_hint, policy FROM records WHERE id=?",
                (record_id,),
            ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return self._row_to_record(row)

    def get_ciphertext(self, record_id: str) -> Tuple[bytes, bytes]:
        """Return the encrypted payload and nonce for a record."""

        with self._lock:
            row = self._conn.execute(
                "SELECT enc_priv, nonce FROM records WHERE id=?", (record_id,)
            ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return row["enc_priv"], row["nonce"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> VaultRecord:
        tags = json.loads(row["tags"]) if row["tags"] else []
        policy_data = json.loads(row["policy"])
        return VaultRecord(
            id=row["id"],
            label=row["label"],
            fmt=row["fmt"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            use_count=row["use_count"],
            tags=tags,
            entropy_hint=row["entropy_hint"],
            policy=VaultPolicy.model_validate(policy_data),
        )

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()
