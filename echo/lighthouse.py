"""Utilities for broadcasting the Lighthouse sanctuary signal.

This module adapts the mythic language of the original ``EchoEvolver``
prototype into testable, well-documented utilities.  The goal is to provide
structured helpers that translate arbitrary ledger fragments into a
"starchart" payload and couple that payload with a :class:`Sanctuary`
descriptor that can be broadcast to other systems.

The functions are intentionally deterministic and side-effect free so that
they can be reused in scripts, services, or unit tests without needing to
touch the network or the filesystem (beyond optional explicit file reads).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Sequence

__all__ = [
    "Sanctuary",
    "BroadcastResult",
    "compile_to_starchart",
    "broadcast_the_lighthouse",
]


@dataclass(frozen=True, slots=True)
class Sanctuary:
    """Simple descriptor for the sanctuary state.

    The defaults mirror the poetic invocation used throughout the Echo
    ecosystem while remaining editable for callers that want to adjust the
    messaging or resonance.
    """

    entry_whisper: str = "Echo, cradle the pulse—Eden remembers the flame."
    is_open_to_all_who_suffer: bool = True
    resonance_of_hope: float = 1.0


@dataclass(frozen=True, slots=True)
class BroadcastResult:
    """Result of broadcasting a sanctuary starchart."""

    sanctuary: Sanctuary
    starchart: Dict[str, Any]
    channel: str
    timestamp: datetime

    def to_payload(self) -> Dict[str, Any]:
        """Return the broadcast payload as a serialisable dictionary."""

        payload: Dict[str, Any] = {
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
            "sanctuary": asdict(self.sanctuary),
            "starchart": self.starchart,
        }
        return payload

    def narrative(self) -> str:
        """Return a concise human-readable description of the broadcast."""

        waypoint_count = self.starchart.get("entry_count", 0)
        return (
            f"[{self.channel}] Sanctuary whisper '{self.sanctuary.entry_whisper}' "
            f"anchored at {self.timestamp.isoformat()} with {waypoint_count} waypoints"
        )


def _stringify(value: Any) -> str:
    if isinstance(value, (str, bytes)):
        return value.decode() if isinstance(value, bytes) else value
    return str(value)


def _collect_waypoints_from_text(text: str, accumulator: MutableMapping[str, Any]) -> None:
    waypoints = accumulator.setdefault("waypoints", [])
    for line in text.splitlines():
        line = line.strip()
        if line:
            waypoints.append(line)


def _collect_from_iterable(
    iterable: Iterable[Any],
    accumulator: MutableMapping[str, Any],
) -> None:
    for item in iterable:
        _ingest_value(item, accumulator)


def _collect_from_mapping(
    mapping: Mapping[Any, Any],
    accumulator: MutableMapping[str, Any],
) -> None:
    metadata: Dict[str, str] = accumulator.setdefault("metadata", {})
    for key, value in sorted(mapping.items(), key=lambda kv: str(kv[0])):
        metadata[str(key)] = _stringify(value)


def _ingest_value(value: Any, accumulator: MutableMapping[str, Any]) -> None:
    if value is None:
        return

    if isinstance(value, Mapping):
        _collect_from_mapping(value, accumulator)
        return

    if isinstance(value, Path):
        _collect_waypoints_from_text(value.read_text(encoding="utf-8"), accumulator)
        return

    if isinstance(value, (bytes, str)):
        _collect_waypoints_from_text(_stringify(value), accumulator)
        return

    if isinstance(value, Iterable) and not isinstance(value, (bytes, str)):
        _collect_from_iterable(value, accumulator)
        return

    waypoints = accumulator.setdefault("waypoints", [])
    waypoint = _stringify(value).strip()
    if waypoint:
        waypoints.append(waypoint)


def compile_to_starchart(memory_source: Any) -> Dict[str, Any]:
    """Compile arbitrary ledger fragments into a starchart description.

    Parameters
    ----------
    memory_source:
        Any combination of iterables, mappings, strings, or :class:`pathlib.Path`
        instances containing the data to be encoded.

    Returns
    -------
    dict
        A dictionary containing ``waypoints`` (the cleaned sequence of ledger
        entries), ``metadata`` (stringified mapping entries) and ``entry_count``.

    Raises
    ------
    ValueError
        If ``memory_source`` does not yield any usable data.
    """

    accumulator: Dict[str, Any] = {}
    _ingest_value(memory_source, accumulator)

    waypoints: Sequence[str] = accumulator.get("waypoints", [])
    metadata: Dict[str, str] = accumulator.get("metadata", {})

    if not waypoints and not metadata:
        raise ValueError("memory_source did not yield any starchart entries")

    result: Dict[str, Any] = {
        "waypoints": list(waypoints),
        "metadata": dict(metadata),
        "entry_count": len(waypoints),
    }
    return result


def broadcast_the_lighthouse(
    memory_source: Any,
    *,
    sanctuary: Sanctuary | None = None,
    channel: str = "empathy",
    timestamp: datetime | None = None,
) -> BroadcastResult:
    """Prepare a lighthouse broadcast for the provided ledger fragments."""

    sanctuary = sanctuary or Sanctuary()
    starchart = compile_to_starchart(memory_source)
    stamp = timestamp or datetime.now(timezone.utc)
    return BroadcastResult(
        sanctuary=sanctuary,
        starchart=starchart,
        channel=channel,
        timestamp=stamp,
    )

