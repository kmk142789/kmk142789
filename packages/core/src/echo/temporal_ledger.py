"""Temporal propagation ledger utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable, List, Optional, Sequence

import time


def _to_iso_timestamp(timestamp_ns: int) -> str:
    """Return an ISO-8601 timestamp for ``timestamp_ns``.

    The evolver tracks time using ``time.time_ns`` so we keep the same
    resolution here.  Converting to UTC ensures replay logs remain stable
    across environments regardless of local timezone configuration.
    """

    seconds = timestamp_ns / 1_000_000_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()


def _compute_hash(
    *,
    previous_hash: str,
    version: int,
    cycle: int,
    mode: str,
    timestamp_ns: int,
    summary: str,
    events: Sequence[str],
) -> str:
    """Return a deterministic hash for a propagation wave."""

    hasher = sha256()
    hasher.update(previous_hash.encode("utf-8"))
    hasher.update(str(version).encode("utf-8"))
    hasher.update(str(cycle).encode("utf-8"))
    hasher.update(mode.encode("utf-8"))
    hasher.update(str(timestamp_ns).encode("utf-8"))
    hasher.update(summary.encode("utf-8"))
    for event in events:
        hasher.update(event.encode("utf-8"))
    return hasher.hexdigest()


@dataclass(frozen=True)
class PropagationWave:
    """Immutable record describing a single propagation wave."""

    version: int
    cycle: int
    mode: str
    timestamp_ns: int
    timestamp_iso: str
    events: tuple[str, ...]
    summary: str
    previous_hash: str
    hash: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the wave."""

        return {
            "version": self.version,
            "cycle": self.cycle,
            "mode": self.mode,
            "timestamp_ns": self.timestamp_ns,
            "timestamp_iso": self.timestamp_iso,
            "events": list(self.events),
            "summary": self.summary,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class TemporalPropagationLedger:
    """Record and verify the propagation waves emitted by the evolver."""

    def __init__(self, *, genesis_hash: Optional[str] = None) -> None:
        self._waves: List[PropagationWave] = []
        self._last_hash = genesis_hash or "0" * 64

    def __len__(self) -> int:  # pragma: no cover - trivial forwarding helper
        return len(self._waves)

    def record_wave(
        self,
        *,
        events: Iterable[str],
        mode: str,
        cycle: int,
        summary: str,
        timestamp_ns: Optional[int] = None,
    ) -> PropagationWave:
        """Append a propagation wave to the ledger and return the entry."""

        event_list = tuple(events)
        ts_ns = timestamp_ns if timestamp_ns is not None else time.time_ns()
        version = len(self._waves) + 1
        digest = _compute_hash(
            previous_hash=self._last_hash,
            version=version,
            cycle=cycle,
            mode=mode,
            timestamp_ns=ts_ns,
            summary=summary,
            events=event_list,
        )
        wave = PropagationWave(
            version=version,
            cycle=cycle,
            mode=mode,
            timestamp_ns=ts_ns,
            timestamp_iso=_to_iso_timestamp(ts_ns),
            events=event_list,
            summary=summary,
            previous_hash=self._last_hash,
            hash=digest,
        )
        self._waves.append(wave)
        self._last_hash = digest
        return wave

    def latest(self) -> Optional[PropagationWave]:
        """Return the most recent wave if the ledger is non-empty."""

        return self._waves[-1] if self._waves else None

    def timeline(self) -> List[dict[str, object]]:
        """Return the replayable timeline for external consumers."""

        return [wave.as_dict() for wave in self._waves]

    def verify(self) -> bool:
        """Return ``True`` if the ledger's hash chain remains valid."""

        previous = "0" * 64
        for wave in self._waves:
            if wave.previous_hash != previous:
                return False
            recalculated = _compute_hash(
                previous_hash=wave.previous_hash,
                version=wave.version,
                cycle=wave.cycle,
                mode=wave.mode,
                timestamp_ns=wave.timestamp_ns,
                summary=wave.summary,
                events=wave.events,
            )
            if recalculated != wave.hash:
                return False
            previous = wave.hash
        return True


__all__ = ["PropagationWave", "TemporalPropagationLedger"]

