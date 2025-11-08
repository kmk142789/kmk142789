"""Temporal propagation ledger utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable, List, Optional, Sequence, TYPE_CHECKING

from uuid import uuid4

import time

from echo.atlas.temporal_ledger import (
    ConsensusRound,
    LedgerEntry,
    QuorumMembership,
    VotePayload,
)

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from echo.atlas.temporal_ledger import LedgerEntryInput


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


class TemporalConsensusFabric:
    """Coordinate consensus rounds before emitting propagation waves."""

    def __init__(
        self,
        *,
        propagation_ledger: TemporalPropagationLedger,
        quorum_members: Sequence[str],
        threshold: float,
        default_mode: str = "consensus",
    ) -> None:
        self._propagation_ledger = propagation_ledger
        self._quorum_members = tuple(dict.fromkeys(quorum_members))
        self._threshold = float(threshold)
        self._default_mode = default_mode
        self._current_round_id: str | None = None
        self._opened_at: datetime | None = None
        self._phase: str = "idle"
        self._votes: dict[str, VotePayload] = {}
        self._events: list[str] = []
        self._latest_snapshot: ConsensusRound | None = None
        self._last_completed_round: ConsensusRound | None = None

    @property
    def current_round_id(self) -> str | None:
        """Return the identifier for the active consensus round if present."""

        return self._current_round_id

    @property
    def last_completed_round(self) -> ConsensusRound | None:
        """Return the most recent finalized consensus round snapshot if any."""

        return self._last_completed_round

    def ensure_round(self, *, round_id: str | None = None, phase: str = "collecting") -> ConsensusRound:
        """Ensure an active round exists and return its snapshot."""

        if self._current_round_id is None:
            return self.schedule_round(round_id=round_id, phase=phase)
        return self._active_snapshot()

    def schedule_round(self, *, round_id: str | None = None, phase: str = "collecting") -> ConsensusRound:
        """Start a new consensus round resetting votes and buffered events."""

        self._current_round_id = round_id or uuid4().hex
        self._opened_at = datetime.now(timezone.utc)
        self._phase = phase
        self._votes.clear()
        self._events.clear()
        self._latest_snapshot = self._build_snapshot()
        return self._latest_snapshot

    def register_vote(self, vote: VotePayload) -> ConsensusRound:
        """Register or replace a vote for the active consensus round."""

        self.ensure_round()
        self._votes[vote.voter] = vote
        self._latest_snapshot = self._build_snapshot()
        if self._latest_snapshot.tally >= self._latest_snapshot.quorum.threshold:
            self._phase = "quorum-achieved"
            self._latest_snapshot = self._build_snapshot()
        return self._latest_snapshot

    def record_event(self, event_token: str) -> ConsensusRound | None:
        """Attach an event token to the active round and return the snapshot."""

        if self._current_round_id is None:
            return None
        self._events.append(event_token)
        self._latest_snapshot = self._build_snapshot()
        return self._latest_snapshot

    def record_ledger_entry(self, entry: LedgerEntry) -> ConsensusRound | None:
        """Shortcut to record the hash of a newly appended ledger entry."""

        return self.record_event(entry.hash)

    def annotate_entry(self, entry: "LedgerEntryInput") -> "LedgerEntryInput":
        """Return a copy of ``entry`` enriched with the current consensus snapshot."""

        snapshot = self._active_snapshot()
        if snapshot is None:
            return entry
        return entry.model_copy(update={"consensus_round": snapshot})

    @property
    def quorum_reached(self) -> bool:
        """Return ``True`` when the active round has satisfied its threshold."""

        snapshot = self._active_snapshot()
        return bool(snapshot and snapshot.tally >= snapshot.quorum.threshold)

    def publish_wave(
        self,
        *,
        summary: str,
        mode: Optional[str] = None,
        cycle: Optional[int] = None,
        events: Sequence[str] | None = None,
        timestamp_ns: Optional[int] = None,
    ) -> PropagationWave:
        """Finalize the round and emit a propagation wave entry."""

        snapshot = self._active_snapshot()
        if snapshot is None:
            raise RuntimeError("No active consensus round to publish")
        if snapshot.tally < snapshot.quorum.threshold:
            raise RuntimeError("Cannot publish propagation wave before quorum is met")

        self._phase = "finalized"
        closed_at = datetime.now(timezone.utc)
        final_snapshot = self._build_snapshot(closed_at=closed_at)

        wave_events = tuple(events) if events is not None else tuple(self._events)
        if not wave_events:
            wave_events = tuple(snapshot.events)
        mode_value = mode or self._default_mode
        cycle_value = cycle if cycle is not None else len(self._propagation_ledger) + 1

        wave = self._propagation_ledger.record_wave(
            events=wave_events,
            mode=mode_value,
            cycle=cycle_value,
            summary=summary,
            timestamp_ns=timestamp_ns,
        )

        self._last_completed_round = final_snapshot
        self._current_round_id = None
        self._opened_at = None
        self._phase = "idle"
        self._votes.clear()
        self._events.clear()
        self._latest_snapshot = None
        return wave

    def _active_snapshot(self) -> ConsensusRound | None:
        if self._current_round_id is None or self._opened_at is None:
            return None
        if self._latest_snapshot is None or self._latest_snapshot.round_id != self._current_round_id:
            self._latest_snapshot = self._build_snapshot()
        return self._latest_snapshot

    def _build_snapshot(self, *, closed_at: datetime | None = None) -> ConsensusRound:
        if self._current_round_id is None or self._opened_at is None:
            raise RuntimeError("Cannot build snapshot without an active round")
        votes = tuple(sorted(self._votes.values(), key=lambda vote: vote.voter))
        tally = float(sum(vote.weight for vote in votes))
        quorum = QuorumMembership(members=self._quorum_members, threshold=self._threshold)
        events = tuple(self._events)
        if closed_at is None and self._phase == "finalized":
            closed_at = datetime.now(timezone.utc)
        return ConsensusRound(
            round_id=self._current_round_id,
            phase=self._phase,
            opened_at=self._opened_at,
            closed_at=closed_at,
            quorum=quorum,
            votes=votes,
            events=events,
            tally=tally,
        )


__all__ = ["PropagationWave", "TemporalPropagationLedger", "TemporalConsensusFabric"]

