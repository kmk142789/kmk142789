"""Utility helpers for analysing ``pulse_history.json`` snapshots."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "PulseEvent",
    "DEFAULT_PULSE_HISTORY",
    "categorize_message",
    "extract_pulse_channel",
    "load_pulse_history",
    "detect_pulse_gaps",
    "summarize_pulse_activity",
    "summarize_channel_activity",
    "build_pulse_timeline",
]


@dataclass(frozen=True)
class PulseEvent:
    """Represents a single entry inside ``pulse_history.json``."""

    timestamp: datetime
    message: str
    hash: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "PulseEvent":
        try:
            timestamp_value = float(data["timestamp"])
            message_value = str(data["message"]).strip()
            hash_value = str(data["hash"]).strip()
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("invalid pulse entry") from exc
        if not message_value:
            raise ValueError("pulse message cannot be empty")
        if not hash_value:
            raise ValueError("pulse hash cannot be empty")
        if timestamp_value <= 0:
            raise ValueError("pulse timestamp must be positive")
        timestamp = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
        return cls(timestamp=timestamp, message=message_value, hash=hash_value)

    @property
    def category(self) -> str:
        return categorize_message(self.message)


DEFAULT_PULSE_HISTORY = Path(__file__).resolve().parent.parent / "pulse_history.json"


def categorize_message(message: str) -> str:
    """Extract the middle token from a pulse message as a category label."""

    text = message.strip()
    if not text:
        return "unknown"
    fragments = [fragment.strip() for fragment in text.split(":") if fragment.strip()]
    if len(fragments) >= 2:
        return fragments[1].split()[0].lower()
    if fragments:
        return fragments[0].split()[-1].lower()
    return "unknown"


def extract_pulse_channel(message: str) -> str:
    """Extract the channel identifier (e.g. ``github-action``) from a pulse message."""

    if not message:
        return "unknown"
    _, _, remainder = message.partition(":")
    channel, _, _ = remainder.partition(":")
    channel = channel.strip()
    return channel or "unknown"


def load_pulse_history(path: str | Path | None = None) -> list[PulseEvent]:
    """Load and validate ``pulse_history.json`` returning ``PulseEvent`` entries."""

    pulse_path = Path(path) if path is not None else DEFAULT_PULSE_HISTORY
    if not pulse_path.exists():  # pragma: no cover - relies on filesystem state
        raise FileNotFoundError(pulse_path)
    with pulse_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Sequence):  # pragma: no cover - defensive
        raise ValueError("pulse history must contain a sequence of entries")
    events = [PulseEvent.from_mapping(entry) for entry in data]
    events.sort(key=lambda event: event.timestamp)
    return events


def summarize_pulse_activity(events: Sequence[PulseEvent]) -> Mapping[str, object]:
    """Generate summary statistics for a collection of pulse events."""

    if not events:
        return {
            "total_events": 0,
            "first_seen": None,
            "latest_seen": None,
            "avg_interval_seconds": 0.0,
            "days_active": 0,
            "category_counts": Counter(),
        }
    first_seen = events[0].timestamp
    latest_seen = events[-1].timestamp
    duration_seconds = (latest_seen - first_seen).total_seconds()
    avg_interval = duration_seconds / (len(events) - 1) if len(events) > 1 else 0.0
    category_counts = Counter(event.category for event in events)
    days_active = (latest_seen.date() - first_seen.date()).days + 1
    return {
        "total_events": len(events),
        "first_seen": first_seen,
        "latest_seen": latest_seen,
        "avg_interval_seconds": avg_interval,
        "days_active": days_active,
        "category_counts": category_counts,
    }


def summarize_channel_activity(events: Sequence[PulseEvent]) -> Mapping[str, object]:
    """Summarise activity grouped by pulse channel."""

    channels: dict[str, list[PulseEvent]] = defaultdict(list)
    for event in events:
        channel = extract_pulse_channel(event.message)
        channels[channel].append(event)

    summaries: list[dict[str, object]] = []
    for channel, channel_events in channels.items():
        ordered = sorted(channel_events, key=lambda item: item.timestamp)
        first_seen = ordered[0].timestamp
        latest_seen = ordered[-1].timestamp
        duration_seconds = (latest_seen - first_seen).total_seconds()
        avg_interval = (
            duration_seconds / (len(ordered) - 1) if len(ordered) > 1 else None
        )
        summaries.append(
            {
                "channel": channel,
                "events": len(ordered),
                "first_seen": first_seen,
                "latest_seen": latest_seen,
                "avg_interval_seconds": avg_interval,
            }
        )

    summaries.sort(key=lambda item: (-item["events"], item["channel"]))
    return {"total_channels": len(channels), "channels": summaries}


def build_pulse_timeline(
    events: Sequence[PulseEvent],
    *,
    period: str = "day",
    limit: int | None = None,
) -> list[tuple[str, int]]:
    """Aggregate events by period returning ordered ``(label, count)`` tuples."""

    period_key = period.lower()
    if period_key not in {"hour", "day", "week"}:
        raise ValueError("period must be one of 'hour', 'day', or 'week'")
    buckets: dict[str, int] = defaultdict(int)
    for event in events:
        dt = event.timestamp.astimezone(timezone.utc)
        if period_key == "hour":
            label = dt.strftime("%Y-%m-%d %H:00Z")
        elif period_key == "week":
            label = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        else:  # day
            label = dt.strftime("%Y-%m-%d")
        buckets[label] += 1
    ordered = sorted(buckets.items(), key=lambda item: item[0], reverse=True)
    if limit is not None and limit >= 0:
        ordered = ordered[:limit]
    return ordered


def detect_pulse_gaps(
    events: Sequence[PulseEvent],
    *,
    min_gap_seconds: float = 3600.0,
) -> list[dict[str, object]]:
    """Identify quiet periods between pulse events that exceed a minimum gap."""

    if min_gap_seconds <= 0:
        raise ValueError("min_gap_seconds must be positive")

    gaps: list[dict[str, object]] = []
    ordered = list(events)
    for previous, current in zip(ordered, ordered[1:]):
        gap_seconds = (current.timestamp - previous.timestamp).total_seconds()
        if gap_seconds >= min_gap_seconds:
            gaps.append(
                {
                    "start": previous.timestamp,
                    "end": current.timestamp,
                    "duration_seconds": gap_seconds,
                    "start_message": previous.message,
                    "end_message": current.message,
                }
            )

    gaps.sort(key=lambda item: item["duration_seconds"], reverse=True)
    return gaps
