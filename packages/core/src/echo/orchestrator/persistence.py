from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class LocalOrchestratorStore:
    """Lightweight SQLite-backed persistence for offline orchestration.

    The store is intentionally minimal so it can operate on low-power devices
    without network access.  It records requests, decisions, results, policies,
    configs, and metrics so the orchestrator can recover state after a reboot
    or during extended offline windows.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._create_schema()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------
    def _create_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                created_at TEXT NOT NULL,
                decision TEXT NOT NULL,
                offline_mode INTEGER DEFAULT 0,
                offline_reason TEXT,
                offline_policy_version TEXT,
                FOREIGN KEY(request_id) REFERENCES requests(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                created_at TEXT NOT NULL,
                result TEXT NOT NULL,
                success INTEGER DEFAULT 1,
                latency_ms REAL,
                error TEXT,
                FOREIGN KEY(decision_id) REFERENCES decisions(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL,
                document TEXT,
                signed_by TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY(policy_id, version)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def log_request(self, payload: Mapping[str, Any]) -> int:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO requests (created_at, payload) VALUES (?, ?)",
            (_utc_now_iso(), json.dumps(payload, ensure_ascii=False, default=str)),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def log_decision(
        self,
        request_id: int | None,
        decision: Mapping[str, Any],
        *,
        offline_mode: bool,
        offline_reason: str | None,
        offline_policy_version: str | None,
    ) -> int:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO decisions (
                request_id, created_at, decision, offline_mode, offline_reason, offline_policy_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                _utc_now_iso(),
                json.dumps(decision, ensure_ascii=False, default=str),
                int(offline_mode),
                offline_reason,
                offline_policy_version,
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def log_result(
        self,
        decision_id: int | None,
        result: Mapping[str, Any],
        *,
        success: bool = True,
        latency_ms: float | None = None,
        error: str | None = None,
    ) -> int:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO results (
                decision_id, created_at, result, success, latency_ms, error
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                _utc_now_iso(),
                json.dumps(result, ensure_ascii=False, default=str),
                int(success),
                latency_ms,
                error,
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def record_metric(
        self, name: str, value: float | None, *, metadata: Mapping[str, Any] | None = None
    ) -> None:
        payload = json.dumps(metadata or {}, ensure_ascii=False, default=str)
        self._conn.execute(
            "INSERT INTO metrics (name, value, metadata, created_at) VALUES (?, ?, ?, ?)",
            (name, value, payload, _utc_now_iso()),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Policies and config
    # ------------------------------------------------------------------
    def set_policy(
        self,
        policy_id: str,
        *,
        version: int,
        status: str = "active",
        document: Mapping[str, Any] | None = None,
        signed_by: str | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO policies (
                policy_id, version, status, document, signed_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                policy_id,
                version,
                status,
                json.dumps(document or {}, ensure_ascii=False, default=str),
                signed_by,
                _utc_now_iso(),
            ),
        )
        self._conn.commit()

    def get_active_policy_version(self) -> str | None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT policy_id, version FROM policies
            WHERE status = 'active'
            ORDER BY version DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return None
        policy_id, version = row
        return f"{policy_id}@v{version}"

    def load_active_policies(self) -> list[MutableMapping[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT policy_id, version, status, document, signed_by, created_at
            FROM policies WHERE status = 'active'
            ORDER BY version DESC
            """
        )
        records = []
        for policy_id, version, status, document, signed_by, created_at in cursor.fetchall():
            payload = json.loads(document or "{}")
            payload.update(
                {
                    "policy_id": policy_id,
                    "version": version,
                    "status": status,
                    "signed_by": signed_by,
                    "created_at": created_at,
                }
            )
            records.append(payload)
        return records

    def set_config(self, key: str, value: Mapping[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value, ensure_ascii=False, default=str), _utc_now_iso()),
        )
        self._conn.commit()

    def load_config(self) -> MutableMapping[str, Any]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        config: MutableMapping[str, Any] = {}
        for key, raw in cursor.fetchall():
            try:
                config[key] = json.loads(raw)
            except json.JSONDecodeError:
                config[key] = raw
        return config

    def latest_metrics(self, *, limit: int = 20) -> list[MutableMapping[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT name, value, metadata, created_at FROM metrics
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        metrics: list[MutableMapping[str, Any]] = []
        for name, value, metadata, created_at in cursor.fetchall():
            try:
                parsed_metadata = json.loads(metadata or "{}")
            except json.JSONDecodeError:
                parsed_metadata = {"raw": metadata}
            metrics.append(
                {
                    "name": name,
                    "value": value,
                    "metadata": parsed_metadata,
                    "created_at": created_at,
                }
            )
        return metrics

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------
    def snapshot_state(self) -> Mapping[str, Any]:
        return {
            "policies": self.load_active_policies(),
            "config": self.load_config(),
            "metrics": self.latest_metrics(limit=50),
        }

    def close(self) -> None:
        self._conn.close()

