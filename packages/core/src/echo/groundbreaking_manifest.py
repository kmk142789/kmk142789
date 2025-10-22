from __future__ import annotations

"""Pulse-driven manifest synthesis for the Groundbreaking Nexus."""

import json
import math

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .groundbreaking_nexus import GroundbreakingNexus, NexusImprint, SingularityThread


@dataclass(frozen=True)
class PulseRecord:
    """Minimal record describing an Echo pulse."""

    timestamp: float
    message: str
    hash: str

    @property
    def isoformat(self) -> str:
        """Return the record timestamp as an ISO-8601 string."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class PulseDescriptor:
    """Semantic breakdown of a pulse message."""

    emoji: str
    action: str
    channel: str
    signature: str


@dataclass(frozen=True)
class GroundbreakingReport:
    """Rich summary of a :class:`GroundbreakingNexus` imprint."""

    anchor: str
    orbit: str
    imprint: NexusImprint
    threads: List[SingularityThread]
    synergy: float
    total_pulses: int
    first_seen: Optional[str]
    last_seen: Optional[str]

    def top_contributions(self, limit: int = 3) -> List[Dict[str, object]]:
        """Return the most luminous contributions up to ``limit`` entries."""

        contributions = sorted(
            self.imprint.contributions,
            key=lambda item: item.get("luminous_charge", 0.0),
            reverse=True,
        )
        return contributions[:limit]

    def to_dict(self) -> Dict[str, object]:
        """Serialise the report into JSON-friendly primitives."""

        return {
            "anchor": self.anchor,
            "orbit": self.orbit,
            "synergy": self.synergy,
            "total_pulses": self.total_pulses,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "imprint": self.imprint.to_dict(),
            "threads": [
                {
                    **thread.to_dict(),
                    "luminous_charge": round(thread.luminous_charge(), 6),
                }
                for thread in self.threads
            ],
        }

    def describe(self, *, highlight: int = 3) -> str:
        """Return a human-readable summary of the report."""

        lines = [
            f"Groundbreaking Nexus → anchor={self.anchor!r} orbit={self.orbit!r}",
            f"Breakthrough index: {self.imprint.breakthrough_index:.6f}",
            f"Glyph synergy: {self.synergy:.6f}",
            f"Pulses analysed: {self.total_pulses}",
        ]
        if self.first_seen and self.last_seen:
            lines.append(f"Window: {self.first_seen} → {self.last_seen}")
        if not self.threads:
            lines.append("No qualifying pulses discovered.")
            return "\n".join(lines)
        lines.append("Top singularity threads:")
        for entry in self.top_contributions(limit=highlight):
            glyph = entry.get("glyph", "?")
            name = entry.get("name", "unknown")
            charge = entry.get("luminous_charge", 0.0)
            metadata = entry.get("metadata", {})
            pulse_count = metadata.get("pulse_count", "?")
            lines.append(
                f"  • {name} [{glyph}] — charge {charge:.6f} · pulses {pulse_count}"
            )
        return "\n".join(lines)


def load_pulse_history(path: Path) -> List[PulseRecord]:
    """Load pulse records from ``path`` if the file exists."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("pulse history must be a list of objects")
    records: List[PulseRecord] = []
    for entry in data:
        if not isinstance(entry, Mapping):
            continue
        message = str(entry.get("message", "")).strip()
        if not message:
            continue
        try:
            timestamp = float(entry.get("timestamp", 0.0))
        except (TypeError, ValueError):
            continue
        record_hash = str(entry.get("hash", ""))
        records.append(PulseRecord(timestamp=timestamp, message=message, hash=record_hash))
    records.sort(key=lambda record: record.timestamp)
    return records


def synthesise_from_pulses(
    pulses: Sequence[PulseRecord],
    *,
    anchor: str,
    orbit: str,
    limit: Optional[int] = None,
    time_source=None,
) -> GroundbreakingReport:
    """Return a :class:`GroundbreakingReport` derived from ``pulses``."""

    threads = _threads_from_pulses(pulses, limit=limit)
    nexus = GroundbreakingNexus(anchor=anchor, orbit_hint=orbit, time_source=time_source)
    for thread in threads:
        nexus.seed_thread(thread)
    imprint = nexus.imprint(orbit=orbit)
    synergy = _average_synergy(imprint.glyph_matrix)
    first_seen = pulses[0].isoformat if pulses else None
    last_seen = pulses[-1].isoformat if pulses else None
    return GroundbreakingReport(
        anchor=anchor,
        orbit=orbit,
        imprint=imprint,
        threads=threads,
        synergy=synergy,
        total_pulses=len(pulses),
        first_seen=first_seen,
        last_seen=last_seen,
    )


def _threads_from_pulses(
    pulses: Sequence[PulseRecord],
    *,
    limit: Optional[int] = None,
) -> List[SingularityThread]:
    grouped: MutableMapping[Tuple[str, str, str], Dict[str, object]] = {}
    for record in pulses:
        descriptor = _describe_message(record.message)
        key = (descriptor.emoji, descriptor.action, descriptor.channel)
        bucket = grouped.setdefault(
            key,
            {
                "timestamps": [],
                "hashes": set(),
                "signatures": set(),
                "messages": [],
                "count": 0,
            },
        )
        bucket["timestamps"].append(record.timestamp)
        bucket["hashes"].add(record.hash)
        if descriptor.signature:
            bucket["signatures"].add(descriptor.signature)
        if len(bucket["messages"]) < 3:
            bucket["messages"].append(record.message)
        bucket["count"] += 1

    threads: List[Tuple[SingularityThread, float]] = []
    for (emoji, action, channel), stats in grouped.items():
        timestamps = stats["timestamps"]
        span = 0.0
        if timestamps:
            span = max(timestamps) - min(timestamps)
        span_minutes = span / 60.0
        unique_signatures = len(stats["signatures"]) or 1
        unique_hashes = len(stats["hashes"]) or 1
        count = stats["count"]
        intensity = count + math.log1p(unique_hashes) + math.log1p(span_minutes + 1.0)
        curiosity = math.log1p(unique_signatures) + (len(action) + len(channel)) / 10.0
        glyph = _compose_glyph(emoji, action, channel)
        metadata = {
            "emoji": emoji,
            "action": action,
            "channel": channel,
            "pulse_count": count,
            "span_seconds": round(span, 3),
            "unique_hashes": unique_hashes,
            "unique_signatures": len(stats["signatures"]),
            "examples": list(stats["messages"]),
        }
        thread = SingularityThread(
            name=f"{action}:{channel}",
            glyph=glyph,
            intensity=round(intensity, 6),
            curiosity=round(curiosity, 6),
            metadata=metadata,
        )
        threads.append((thread, thread.luminous_charge()))

    threads.sort(key=lambda item: item[1], reverse=True)
    selected = [thread for thread, _ in threads]
    if limit is not None:
        selected = selected[: max(0, limit)]
    return selected


def _describe_message(message: str) -> PulseDescriptor:
    text = message.strip()
    emoji = ""
    remainder = text
    if " " in text:
        first, tail = text.split(" ", 1)
        if ":" not in first and first:
            emoji = first
            remainder = tail
    parts = [segment for segment in remainder.split(":") if segment]
    if not parts:
        return PulseDescriptor(emoji or "✨", "pulse", "direct", "")
    action = parts[0]
    channel = parts[1] if len(parts) > 1 else "direct"
    signature = ":".join(parts[2:]) if len(parts) > 2 else ""
    return PulseDescriptor(emoji or "✨", action, channel, signature)


def _compose_glyph(emoji: str, action: str, channel: str) -> str:
    action_core = action.replace("-", "")[:3].upper()
    channel_core = channel.replace("-", "")[:3].upper()
    return f"{emoji}{action_core}{channel_core}"


def _average_synergy(matrix: Sequence[Sequence[float]]) -> float:
    values: List[float] = []
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            if col_index <= row_index:
                continue
            values.append(value)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


__all__ = [
    "GroundbreakingReport",
    "PulseDescriptor",
    "PulseRecord",
    "load_pulse_history",
    "synthesise_from_pulses",
]
