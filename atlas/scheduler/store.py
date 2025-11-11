"""Persistence layer for scheduler jobs."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from .job import Job, JobStatus


class JobStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
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
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_schedule ON jobs(status, schedule_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON jobs(tenant, status)")
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def upsert(self, job: Job) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs(id, tenant, payload, schedule_at, status, attempts, last_error, retry_policy, runtime_limit, created_at, updated_at)
                VALUES (:id, :tenant, :payload, :schedule_at, :status, :attempts, :last_error, :retry_policy, :runtime_limit, :created_at, :updated_at)
                ON CONFLICT(id) DO UPDATE SET
                    tenant=excluded.tenant,
                    payload=excluded.payload,
                    schedule_at=excluded.schedule_at,
                    status=excluded.status,
                    attempts=excluded.attempts,
                    last_error=excluded.last_error,
                    retry_policy=excluded.retry_policy,
                    runtime_limit=excluded.runtime_limit,
                    updated_at=excluded.updated_at
                """,
                job.to_record(),
            )
            conn.commit()

    def get_due_jobs(self, limit: int = 50) -> List[Job]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE status = ? AND schedule_at <= ?
                ORDER BY schedule_at ASC
                LIMIT ?
                """,
                (JobStatus.PENDING.value, now, limit),
            ).fetchall()
        return [Job.from_record(dict(row)) for row in rows]

    def mark_running(self, job_id: str) -> None:
        self._update_status(job_id, JobStatus.RUNNING)

    def mark_completed(self, job_id: str) -> None:
        self._update_status(job_id, JobStatus.COMPLETED)

    def mark_failed(self, job: Job, error: str) -> None:
        job.last_error = error
        job.updated_at = datetime.now(timezone.utc)
        if job.attempts >= job.retry_policy.max_attempts:
            job.status = JobStatus.DEAD_LETTER
        self.upsert(job)

    def _update_status(self, job_id: str, status: JobStatus) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?
                """,
                (status.value, datetime.now(timezone.utc).isoformat(), job_id),
            )
            conn.commit()

    def count_active_for_tenant(self, tenant: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE tenant = ? AND status IN (?, ?)",
                (tenant, JobStatus.PENDING.value, JobStatus.RUNNING.value),
            ).fetchone()
        return int(row[0]) if row else 0

    def list_dead_letter(self, tenant: Optional[str] = None) -> List[Job]:
        query = "SELECT * FROM jobs WHERE status = ?"
        params: List[object] = [JobStatus.DEAD_LETTER.value]
        if tenant:
            query += " AND tenant = ?"
            params.append(tenant)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Job.from_record(dict(row)) for row in rows]


__all__ = ["JobStore"]
