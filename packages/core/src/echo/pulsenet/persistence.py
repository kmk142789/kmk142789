"""Persistence helpers for PulseNet pulse events."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from .models import PulseHistoryEntry


_XPUB_RE = re.compile(r"(xpub[1-9A-Za-z]+)")
_FINGERPRINT_RE = re.compile(r"fingerprint[\s:=]+([0-9A-Fa-f]{4,})")
_ATTESTATION_RE = re.compile(r"attest(?:ation)?[_\-\s:=]+([0-9A-Za-z\-]{6,})", re.IGNORECASE)


@dataclass(slots=True)
class PulseEventRecord:
    """Row persisted in the pulse event store."""

    id: int
    timestamp: float
    message: str
    pulse_hash: str | None
    attestation_id: str | None
    attestation_hash: str | None
    actor: str | None
    action: str | None
    ref: str | None
    proof_id: str | None
    xpub: str | None
    fingerprint: str | None
    metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "timestamp": self.timestamp,
            "message": self.message,
            "hash": self.pulse_hash,
            "attestation": {
                "id": self.attestation_id,
                "hash": self.attestation_hash,
                "actor": self.actor,
                "action": self.action,
                "ref": self.ref,
                "proof_id": self.proof_id,
            },
            "metadata": dict(self.metadata),
        }
        if self.xpub:
            payload["xpub"] = self.xpub
        if self.fingerprint:
            payload["fingerprint"] = self.fingerprint
        return payload


class PulseEventStore:
    """SQLite-backed persistence for pulse events and attestations."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def record(
        self,
        entry: PulseHistoryEntry,
        attestation: Mapping[str, Any],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Persist ``entry`` and ``attestation`` if not already recorded."""

        enriched = self._extract_metadata(entry, attestation, metadata)
        with self._lock:
            with self._connect() as conn:
                if self._exists(conn, entry.hash, attestation.get("id")):
                    return
                conn.execute(
                    """
                    INSERT INTO pulse_events (
                        ts,
                        message,
                        pulse_hash,
                        attestation_id,
                        attestation_hash,
                        actor,
                        action,
                        ref,
                        proof_id,
                        xpub,
                        fingerprint,
                        metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.timestamp,
                        entry.message,
                        entry.hash,
                        enriched.get("attestation_id"),
                        attestation.get("hash"),
                        attestation.get("actor"),
                        attestation.get("action"),
                        attestation.get("ref"),
                        attestation.get("proof_id"),
                        enriched.get("xpub"),
                        enriched.get("fingerprint"),
                        json.dumps(enriched, sort_keys=True),
                    ),
                )

    def replay(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        xpub: str | None = None,
        fingerprint: str | None = None,
        attestation_id: str | None = None,
    ) -> list[PulseEventRecord]:
        """Return stored events ordered by timestamp."""

        query = [
            "SELECT id, ts, message, pulse_hash, attestation_id, attestation_hash,",
            "actor, action, ref, proof_id, xpub, fingerprint, metadata",
            "FROM pulse_events",
        ]
        clauses: list[str] = []
        params: list[Any] = []
        if xpub:
            clauses.append("xpub = ?")
            params.append(xpub)
        if fingerprint:
            clauses.append("fingerprint = ?")
            params.append(fingerprint)
        if attestation_id:
            clauses.append("attestation_id = ?")
            params.append(attestation_id)
        if clauses:
            query.append("WHERE " + " AND ".join(clauses))
        query.append("ORDER BY ts ASC, id ASC")
        if limit is not None:
            query.append("LIMIT ? OFFSET ?")
            params.extend([limit, max(0, offset)])
        sql = " ".join(query)
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pulse_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    message TEXT NOT NULL,
                    pulse_hash TEXT,
                    attestation_id TEXT,
                    attestation_hash TEXT,
                    actor TEXT,
                    action TEXT,
                    ref TEXT,
                    proof_id TEXT,
                    xpub TEXT,
                    fingerprint TEXT,
                    metadata TEXT NOT NULL
                )
                """,
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pulse_events_ts ON pulse_events (ts ASC)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pulse_events_hash ON pulse_events (pulse_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pulse_events_attestation_id ON pulse_events (attestation_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pulse_events_xpub ON pulse_events (xpub)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pulse_events_fingerprint ON pulse_events (fingerprint)"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> PulseEventRecord:
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return PulseEventRecord(
            id=int(row["id"]),
            timestamp=float(row["ts"]),
            message=str(row["message"]),
            pulse_hash=row["pulse_hash"],
            attestation_id=row["attestation_id"],
            attestation_hash=row["attestation_hash"],
            actor=row["actor"],
            action=row["action"],
            ref=row["ref"],
            proof_id=row["proof_id"],
            xpub=row["xpub"],
            fingerprint=row["fingerprint"],
            metadata=metadata,
        )

    @staticmethod
    def _exists(conn: sqlite3.Connection, pulse_hash: str | None, attestation_id: str | None) -> bool:
        if pulse_hash:
            cur = conn.execute(
                "SELECT 1 FROM pulse_events WHERE pulse_hash = ? LIMIT 1",
                (pulse_hash,),
            )
            if cur.fetchone():
                return True
        if attestation_id:
            cur = conn.execute(
                "SELECT 1 FROM pulse_events WHERE attestation_id = ? LIMIT 1",
                (attestation_id,),
            )
            if cur.fetchone():
                return True
        return False

    @staticmethod
    def _extract_metadata(
        entry: PulseHistoryEntry,
        attestation: Mapping[str, Any],
        metadata: Mapping[str, Any] | None,
    ) -> MutableMapping[str, Any]:
        result: MutableMapping[str, Any] = {
            "attestation_id": attestation.get("id"),
            "attestation_hash": attestation.get("hash"),
            "proof_id": attestation.get("proof_id"),
        }
        if metadata:
            for key, value in metadata.items():
                if value is None:
                    continue
                result[key] = value
        for key, value in PulseEventStore._metadata_from_message(entry.message).items():
            result.setdefault(key, value)
        if "xpub" not in result:
            if attestation.get("ref") and isinstance(attestation["ref"], str):
                match = _XPUB_RE.search(attestation["ref"])
                if match:
                    result["xpub"] = match.group(1)
        if "attestation_id" not in result and attestation.get("id"):
            result["attestation_id"] = attestation["id"]
        return result

    @staticmethod
    def _metadata_from_message(message: str) -> Mapping[str, Any]:
        payload: MutableMapping[str, Any] = {}
        if not message:
            return payload
        message = message.strip()
        if message.startswith("{") or message.startswith("["):
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, Mapping):
                for key in ("xpub", "fingerprint", "attestation_id", "attestation"):
                    if key in data and data[key]:
                        payload[key if key != "attestation" else "attestation_id"] = str(data[key])
                return payload
        xpub_match = _XPUB_RE.search(message)
        if xpub_match:
            payload["xpub"] = xpub_match.group(1)
        fingerprint_match = _FINGERPRINT_RE.search(message)
        if fingerprint_match:
            payload["fingerprint"] = fingerprint_match.group(1)
        attestation_match = _ATTESTATION_RE.search(message)
        if attestation_match:
            payload["attestation_id"] = attestation_match.group(1)
        return payload


__all__ = ["PulseEventRecord", "PulseEventStore"]
