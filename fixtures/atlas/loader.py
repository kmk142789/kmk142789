"""Helpers for loading deterministic Atlas scheduler fixtures."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from atlas.scheduler.job import Job, JobStatus, RetryPolicy
from atlas.scheduler.store import JobStore

DEFAULT_FIXTURE = Path(__file__).with_name("jobs_default.json")


def _parse_job(record: dict[str, object]) -> Job:
    policy_data = dict(record["retry_policy"])
    retry_policy = RetryPolicy(**policy_data)
    payload_data = dict(record["payload"])
    last_error_value = record.get("last_error")
    return Job(
        id=str(record["id"]),
        tenant=str(record["tenant"]),
        payload=payload_data,
        schedule_at=datetime.fromisoformat(str(record["schedule_at"])),
        status=JobStatus(str(record["status"])),
        attempts=int(record["attempts"]),
        last_error=None if last_error_value is None else str(last_error_value),
        retry_policy=retry_policy,
        runtime_limit=float(record["runtime_limit"]) if record.get("runtime_limit") is not None else None,
        created_at=datetime.fromisoformat(str(record["created_at"])),
        updated_at=datetime.fromisoformat(str(record["updated_at"])),
    )


def load_jobs(db_path: Path, fixture: Path = DEFAULT_FIXTURE) -> List[Job]:
    """Load fixture records into the scheduler database."""

    data = json.loads(fixture.read_text(encoding="utf-8"))
    jobs = [_parse_job(record) for record in data]

    store = JobStore(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM jobs")
        conn.commit()
    for job in jobs:
        store.upsert(job)
    return jobs


def clear_jobs(db_path: Path) -> None:
    """Remove all jobs from the scheduler database."""

    if not db_path.exists():
        return
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM jobs")
        conn.commit()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed Atlas scheduler fixtures")
    parser.add_argument("db", type=Path, help="Path to scheduler database")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Fixture JSON to load",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Only clear jobs without loading fixtures",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.clear:
        clear_jobs(args.db)
    else:
        load_jobs(args.db, args.fixture)


if __name__ == "__main__":
    main()
