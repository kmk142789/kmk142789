"""Persistence helpers for puzzle attestation records."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional

try:  # pragma: no cover - optional dependency for production deployments
    import psycopg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency for production deployments
    psycopg = None  # type: ignore[assignment]


_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass(slots=True)
class PuzzleRecord:
    """Structured representation of a stored puzzle attestation."""

    puzzle_id: int
    payload: Mapping[str, Any]
    checksum: str
    base58: str
    ts: str
    record_hash: str
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "puzzle_id": self.puzzle_id,
            "payload": dict(self.payload),
            "checksum": self.checksum,
            "base58": self.base58,
            "ts": self.ts,
            "record_hash": self.record_hash,
            "created_at": self.created_at,
        }


def encode_base58(data: bytes) -> str:
    """Return the base58 representation of *data*."""

    if not data:
        return ""
    num = int.from_bytes(data, "big")
    encoded = []
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded.append(_ALPHABET[remainder])
    leading = len(data) - len(data.lstrip(b"\0"))
    prefix = "1" * leading
    core = "".join(reversed(encoded)) if encoded else "1"
    return prefix + core


def build_record(puzzle_id: int, payload: Mapping[str, Any]) -> PuzzleRecord:
    """Construct a :class:`PuzzleRecord` and its deterministic hash."""

    timestamp = datetime.now(timezone.utc).isoformat()
    payload_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    base58_value = encode_base58(bytes.fromhex(checksum))
    record_payload = {
        "puzzle_id": puzzle_id,
        "payload": payload,
        "checksum": checksum,
        "base58": base58_value,
        "ts": timestamp,
    }
    record_hash = hashlib.sha256(
        json.dumps(record_payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
    return PuzzleRecord(
        puzzle_id=puzzle_id,
        payload=payload,
        checksum=checksum,
        base58=base58_value,
        ts=timestamp,
        record_hash=record_hash,
    )


class PuzzleAttestationStore:
    """Persist and retrieve puzzle attestation records."""

    def __init__(
        self,
        *,
        database_url: str | None = None,
        fallback_path: Path | None = None,
    ) -> None:
        self._dsn = database_url or os.getenv("DATABASE_URL")
        self._fallback_path = fallback_path or Path.cwd() / "state" / "puzzle_attestations.json"
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: list[PuzzleRecord] = []
        self._db_checked = False
        self._db_available = False
        self._load_fallback()

    # ------------------------------------------------------------------
    # Database management helpers

    def _ensure_database(self) -> None:
        if self._db_checked:
            return
        self._db_checked = True
        if not self._dsn or psycopg is None:
            return
        try:  # pragma: no cover - exercised in integration deployments
            with psycopg.connect(self._dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS puzzle_attestations (
                        puzzle_id INTEGER NOT NULL,
                        payload JSONB NOT NULL,
                        checksum TEXT NOT NULL,
                        base58 TEXT NOT NULL,
                        ts TIMESTAMPTZ NOT NULL,
                        record_hash TEXT PRIMARY KEY,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            self._db_available = True
        except Exception:
            self._db_available = False

    # ------------------------------------------------------------------
    # Fallback cache helpers

    def _load_fallback(self) -> None:
        if not self._fallback_path.exists():
            self._cache = []
            return
        try:
            raw = json.loads(self._fallback_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._cache = []
            return
        records: list[PuzzleRecord] = []
        for item in raw:
            try:
                records.append(
                    PuzzleRecord(
                        puzzle_id=int(item["puzzle_id"]),
                        payload=dict(item["payload"]),
                        checksum=str(item["checksum"]),
                        base58=str(item["base58"]),
                        ts=str(item["ts"]),
                        record_hash=str(item["record_hash"]),
                        created_at=item.get("created_at"),
                    )
                )
            except Exception:
                continue
        records.sort(key=lambda record: record.ts, reverse=True)
        self._cache = records

    def _save_fallback(self) -> None:
        data = [record.to_dict() for record in self._cache]
        self._fallback_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API

    def store(self, record: PuzzleRecord) -> None:
        """Persist *record* to the configured backend and local cache."""

        self._ensure_database()
        if self._db_available and psycopg is not None:  # pragma: no cover - requires Postgres
            try:
                with psycopg.connect(self._dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
                    conn.execute(
                        """
                        INSERT INTO puzzle_attestations (puzzle_id, payload, checksum, base58, ts, record_hash)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (record_hash) DO NOTHING
                        """,
                        (
                            record.puzzle_id,
                            json.dumps(record.payload, sort_keys=True),
                            record.checksum,
                            record.base58,
                            datetime.fromisoformat(record.ts),
                            record.record_hash,
                        ),
                    )
            except Exception:
                self._db_available = False
        with self._lock:
            if record.record_hash in {existing.record_hash for existing in self._cache}:
                return
            self._cache.insert(0, record)
            self._save_fallback()

    def list_for_puzzle(self, puzzle_id: int, *, limit: int | None = None) -> List[PuzzleRecord]:
        """Return stored attestations for *puzzle_id* sorted by recency."""

        self._ensure_database()
        if self._db_available and psycopg is not None:  # pragma: no cover - requires Postgres
            try:
                with psycopg.connect(self._dsn) as conn:  # type: ignore[attr-defined]
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT puzzle_id, payload, checksum, base58, ts, record_hash, created_at
                            FROM puzzle_attestations
                            WHERE puzzle_id = %s
                            ORDER BY ts DESC
                            LIMIT %s
                            """,
                            (puzzle_id, limit or 50),
                        )
                        rows = cur.fetchall()
                records: list[PuzzleRecord] = []
                for row in rows:
                    ts_value = row[4]
                    if hasattr(ts_value, "isoformat"):
                        ts_text = ts_value.isoformat()
                    else:
                        ts_text = str(ts_value)
                    created_at = row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6])
                    payload = row[1]
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except json.JSONDecodeError:
                            payload = {"raw": payload}
                    records.append(
                        PuzzleRecord(
                            puzzle_id=int(row[0]),
                            payload=dict(payload),
                            checksum=str(row[2]),
                            base58=str(row[3]),
                            ts=ts_text,
                            record_hash=str(row[5]),
                            created_at=created_at,
                        )
                    )
                if records:
                    return records
            except Exception:
                self._db_available = False
        results = [record for record in self._cache if record.puzzle_id == puzzle_id]
        if limit is not None:
            return results[:limit]
        return results

    def as_json(self) -> List[dict[str, Any]]:
        """Return the fallback cache as JSON-compatible dictionaries."""

        with self._lock:
            return [record.to_dict() for record in self._cache]


__all__ = ["PuzzleAttestationStore", "PuzzleRecord", "build_record", "encode_base58"]
