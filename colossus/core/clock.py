"""Clock utilities for Colossus."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterator


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone information."""

    return datetime.now(timezone.utc)


def format_timestamp(moment: datetime | None = None) -> str:
    """Format a datetime as an ISO8601 string with millisecond precision."""

    moment = moment or utc_now()
    return moment.astimezone(timezone.utc).strftime(ISO_FORMAT)


def cycle_range(start_cycle: int, count: int) -> Iterator[int]:
    """Yield ``count`` consecutive cycle numbers starting from ``start_cycle``."""

    for offset in range(count):
        yield start_cycle + offset


def cycle_epoch(cycle: int, epoch_duration: timedelta) -> tuple[datetime, datetime]:
    """Return the [start, end) timestamps for a given cycle."""

    start = datetime.fromtimestamp(cycle * epoch_duration.total_seconds(), tz=timezone.utc)
    end = start + epoch_duration
    return start, end


__all__ = [
    "ISO_FORMAT",
    "cycle_epoch",
    "cycle_range",
    "format_timestamp",
    "utc_now",
]
