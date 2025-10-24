"""Pulse signal intensity helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from .._paths import REPO_ROOT

DEFAULT_HISTORY_PATH = REPO_ROOT / "pulse_history.json"


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
    else:
        raise TypeError(f"Unsupported timestamp value: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _bucket_for(timestamp: datetime, interval: timedelta) -> datetime:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = timestamp - epoch
    buckets = int(delta.total_seconds() // interval.total_seconds())
    return epoch + timedelta(seconds=buckets * interval.total_seconds())


@dataclass(frozen=True)
class SignalPoint:
    bucket: datetime
    pulses: int
    repo_activity: int
    threads: int
    merges: int

    @property
    def intensity(self) -> int:
        return self.pulses + self.repo_activity + self.threads + (self.merges * 2)

    def as_dict(self) -> Dict[str, object]:
        return {
            "bucket": self.bucket.isoformat(),
            "pulses": self.pulses,
            "repo_activity": self.repo_activity,
            "threads": self.threads,
            "merges": self.merges,
            "intensity": self.intensity,
        }


def load_pulse_history(path: Path | None = None) -> List[MutableMapping[str, object]]:
    source = path or DEFAULT_HISTORY_PATH
    if not source.exists():
        return []
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def build_signal_series(
    *,
    pulses: Sequence[Mapping[str, object]],
    repo_events: Iterable[datetime] | None = None,
    thread_events: Iterable[datetime] | None = None,
    merge_events: Iterable[datetime] | None = None,
    interval_minutes: int = 60,
) -> List[SignalPoint]:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    interval = timedelta(minutes=interval_minutes)
    counters: Dict[datetime, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for pulse in pulses:
        try:
            ts = _to_datetime(pulse.get("timestamp"))
        except Exception:
            continue
        bucket = _bucket_for(ts, interval)
        counters[bucket]["pulses"] += 1

    def _accumulate(events: Iterable[datetime] | None, key: str) -> None:
        if not events:
            return
        for moment in events:
            bucket = _bucket_for(moment.astimezone(timezone.utc), interval)
            counters[bucket][key] += 1

    _accumulate(repo_events, "repo_activity")
    _accumulate(thread_events, "threads")
    _accumulate(merge_events, "merges")

    points: List[SignalPoint] = []
    for bucket, values in sorted(counters.items(), key=lambda item: item[0]):
        points.append(
            SignalPoint(
                bucket=bucket,
                pulses=values.get("pulses", 0),
                repo_activity=values.get("repo_activity", 0),
                threads=values.get("threads", 0),
                merges=values.get("merges", 0),
            )
        )
    return points


__all__ = ["SignalPoint", "load_pulse_history", "build_signal_series", "DEFAULT_HISTORY_PATH"]

