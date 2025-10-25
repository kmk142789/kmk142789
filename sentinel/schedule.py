from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from .utils import isoformat, utc_now


@dataclass(slots=True)
class Schedule:
    cadence: str
    next_run: str
    description: str


def compute_schedule(interval: timedelta, description: str) -> Schedule:
    return Schedule(
        cadence=f"every {interval.total_seconds()} seconds",
        next_run=isoformat(utc_now() + interval),
        description=description,
    )


def default_schedule() -> list[Schedule]:
    return [
        compute_schedule(timedelta(hours=1), "Verify provenance & probe system state"),
        compute_schedule(timedelta(hours=6), "Re-issue attestations"),
        compute_schedule(timedelta(days=1), "Plan remediation window"),
    ]


def as_dicts(schedules: Iterable[Schedule]) -> list[dict[str, str]]:
    return [schedule.__dict__ for schedule in schedules]


__all__ = ["Schedule", "compute_schedule", "default_schedule", "as_dicts"]

