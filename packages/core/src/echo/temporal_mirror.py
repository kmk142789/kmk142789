"""Temporal mirror synthesis for Echo pulse history."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import time
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class TemporalMirrorPulse:
    original_index: int
    original_timestamp: float
    mirrored_timestamp: float
    message: str
    hash: str
    mirror_hash: str
    offset_seconds: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["original_timestamp"] = round(self.original_timestamp, 6)
        payload["mirrored_timestamp"] = round(self.mirrored_timestamp, 6)
        payload["offset_seconds"] = round(self.offset_seconds, 6)
        payload["original_iso"] = format_iso(self.original_timestamp)
        payload["mirrored_iso"] = format_iso(self.mirrored_timestamp)
        return payload


def format_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def load_pulse_history(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"pulse history not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("pulse history must be a list of entries")
    return data


def _sorted_timestamps(history: Sequence[dict[str, object]]) -> list[float]:
    timestamps: list[float] = []
    for entry in history:
        ts = entry.get("timestamp")
        if isinstance(ts, (int, float)):
            timestamps.append(float(ts))
    timestamps.sort()
    return timestamps


def _derive_intervals(timestamps: Sequence[float], minimum_interval: float) -> list[float]:
    intervals: list[float] = []
    for earlier, later in zip(timestamps, timestamps[1:]):
        interval = max(minimum_interval, later - earlier)
        intervals.append(interval)
    return intervals


def _mirror_hash(source_hash: str, mirrored_timestamp: float, index: int) -> str:
    payload = f"{source_hash}:{mirrored_timestamp:.6f}:{index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_temporal_mirror(
    history: Sequence[dict[str, object]],
    anchor: float | None = None,
    count: int | None = None,
    minimum_interval: float = 1.0,
) -> list[TemporalMirrorPulse]:
    """Create a forward-looking mirror of pulse history intervals."""
    if len(history) < 2:
        raise ValueError("pulse history must include at least two entries to mirror intervals")

    timestamps = _sorted_timestamps(history)
    intervals = _derive_intervals(timestamps, minimum_interval)
    if not intervals:
        raise ValueError("pulse history does not contain usable intervals")

    if count is not None and count > 0:
        intervals = intervals[-count:]
    intervals = list(reversed(intervals))

    anchor_time = anchor if anchor is not None else time.time()

    mirrored: list[TemporalMirrorPulse] = []
    current_time = anchor_time
    for idx, interval in enumerate(intervals):
        current_time += interval
        source_index = len(history) - 1 - idx
        source_entry = history[source_index]
        message = str(source_entry.get("message", ""))
        source_hash = str(source_entry.get("hash", ""))
        mirror_hash = _mirror_hash(source_hash, current_time, idx)
        mirrored.append(
            TemporalMirrorPulse(
                original_index=source_index,
                original_timestamp=float(source_entry.get("timestamp", 0.0)),
                mirrored_timestamp=current_time,
                message=message,
                hash=source_hash,
                mirror_hash=mirror_hash,
                offset_seconds=interval,
            )
        )
    return mirrored


def render_mirror_report(
    pulses: Iterable[TemporalMirrorPulse],
    *,
    anchor: float,
    source: Path,
    world_first_label: str = "World-first temporal mirror cadence",
) -> dict[str, object]:
    pulse_list = list(pulses)
    return {
        "world_first_feature": world_first_label,
        "source": str(source),
        "anchor": round(anchor, 6),
        "anchor_iso": format_iso(anchor),
        "count": len(pulse_list),
        "mirrors": [pulse.to_dict() for pulse in pulse_list],
    }
