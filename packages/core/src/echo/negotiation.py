"""Negotiation lifecycle utilities for Echo counterparties."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Iterable, Mapping, MutableMapping, Sequence

__all__ = [
    "NegotiationError",
    "InvalidTransitionError",
    "UnauthorizedPartyError",
    "RecoveryError",
    "NegotiationPhase",
    "NegotiationEvent",
    "FailureRecord",
    "NegotiationSession",
]


class NegotiationError(RuntimeError):
    """Base error for negotiation lifecycle failures."""


class InvalidTransitionError(NegotiationError):
    """Raised when an invalid state transition is attempted."""


class UnauthorizedPartyError(NegotiationError):
    """Raised when an unknown actor attempts to participate."""


class RecoveryError(NegotiationError):
    """Raised when a recovery attempt cannot be performed."""


class NegotiationPhase(str, Enum):
    """Lifecycle phases emitted as structured events."""

    CREATED = "created"
    PROPOSED = "proposed"
    COUNTERED = "countered"
    AGREED = "agreed"
    DECLINED = "declined"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass(slots=True)
class NegotiationEvent:
    """Structured lifecycle event produced by a negotiation session."""

    timestamp: datetime
    actor: str
    phase: NegotiationPhase
    payload: Mapping[str, object] = field(default_factory=dict)
    note: str | None = None

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the event."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "phase": self.phase.value,
            "payload": dict(self.payload),
            "note": self.note,
        }


@dataclass(slots=True)
class FailureRecord:
    """Metadata captured when a negotiation encounters a failure."""

    timestamp: datetime
    actor: str
    reason: str
    recoverable: bool
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "reason": self.reason,
            "recoverable": self.recoverable,
            "metadata": dict(self.metadata),
        }


class NegotiationSession:
    """Track the lifecycle of a bilateral negotiation."""

    _SYSTEM_ACTORS: frozenset[str] = frozenset({"system"})

    def __init__(
        self,
        session_id: str,
        parties: Sequence[str],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        unique_parties = list(dict.fromkeys(str(party) for party in parties))
        if len(unique_parties) < 2:
            raise ValueError("Negotiation sessions require at least two parties")

        self.session_id = session_id
        self.parties: tuple[str, ...] = tuple(unique_parties)
        self._party_set = frozenset(self.parties)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._state = NegotiationPhase.CREATED
        self._closed = False
        self._history: list[NegotiationEvent] = []
        self._failures: list[FailureRecord] = []
        self._recovery_attempts = 0
        self._active_offer: MutableMapping[str, object] | None = None

        self._record_event(
            "system",
            NegotiationPhase.CREATED,
            payload={"session_id": session_id, "parties": list(self.parties)},
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def state(self) -> NegotiationPhase:
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def history(self) -> tuple[NegotiationEvent, ...]:
        return tuple(self._history)

    @property
    def failure_history(self) -> tuple[FailureRecord, ...]:
        return tuple(self._failures)

    @property
    def recovery_attempts(self) -> int:
        return self._recovery_attempts

    @property
    def current_offer(self) -> MutableMapping[str, object] | None:
        if self._active_offer is None:
            return None
        return {"actor": self._active_offer["actor"], "payload": dict(self._active_offer["payload"])}

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def propose(
        self,
        actor: str,
        proposal: Mapping[str, object],
        *,
        note: str | None = None,
    ) -> NegotiationEvent:
        self._assert_party(actor)
        self._ensure_open()
        if self._state not in {NegotiationPhase.CREATED, NegotiationPhase.RECOVERED}:
            raise InvalidTransitionError(f"Cannot issue proposal in state {self._state.value}")

        self._state = NegotiationPhase.PROPOSED
        self._active_offer = {"actor": actor, "payload": dict(proposal)}
        return self._record_event(
            actor,
            NegotiationPhase.PROPOSED,
            payload={"proposal": dict(proposal)},
            note=note,
        )

    def counter(
        self,
        actor: str,
        proposal: Mapping[str, object],
        *,
        note: str | None = None,
    ) -> NegotiationEvent:
        self._assert_party(actor)
        self._ensure_open()
        if self._state not in {NegotiationPhase.PROPOSED, NegotiationPhase.COUNTERED}:
            raise InvalidTransitionError(f"Cannot counter proposal in state {self._state.value}")

        self._state = NegotiationPhase.COUNTERED
        self._active_offer = {"actor": actor, "payload": dict(proposal)}
        return self._record_event(
            actor,
            NegotiationPhase.COUNTERED,
            payload={"proposal": dict(proposal)},
            note=note,
        )

    def accept(self, actor: str, *, note: str | None = None) -> NegotiationEvent:
        self._assert_party(actor)
        self._ensure_open()
        if self._state not in {NegotiationPhase.PROPOSED, NegotiationPhase.COUNTERED}:
            raise InvalidTransitionError(f"Cannot accept proposal in state {self._state.value}")

        self._state = NegotiationPhase.AGREED
        self._closed = True
        payload: Mapping[str, object] = self._active_offer or {}
        return self._record_event(actor, NegotiationPhase.AGREED, payload=payload, note=note)

    def decline(self, actor: str, reason: str, *, note: str | None = None) -> NegotiationEvent:
        self._assert_party(actor)
        self._ensure_open()
        if self._state not in {NegotiationPhase.PROPOSED, NegotiationPhase.COUNTERED}:
            raise InvalidTransitionError(f"Cannot decline proposal in state {self._state.value}")

        timestamp = self._clock()
        self._register_failure(
            actor,
            reason,
            recoverable=False,
            metadata={"phase": self._state.value},
            timestamp=timestamp,
        )
        self._state = NegotiationPhase.DECLINED
        self._closed = True
        return self._record_event(
            actor,
            NegotiationPhase.DECLINED,
            payload={"reason": reason},
            note=note or reason,
            timestamp=timestamp,
        )

    def fail(
        self,
        actor: str,
        reason: str,
        *,
        recoverable: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> NegotiationEvent:
        if actor not in self._SYSTEM_ACTORS:
            self._assert_party(actor)
        self._ensure_open()
        if self._state not in {NegotiationPhase.PROPOSED, NegotiationPhase.COUNTERED}:
            raise InvalidTransitionError(f"Cannot record failure in state {self._state.value}")

        timestamp = self._clock()
        self._register_failure(
            actor,
            reason,
            recoverable=recoverable,
            metadata=metadata or {},
            timestamp=timestamp,
        )
        self._state = NegotiationPhase.FAILED
        self._closed = not recoverable
        return self._record_event(
            actor,
            NegotiationPhase.FAILED,
            payload={
                "reason": reason,
                "recoverable": recoverable,
                "metadata": dict(metadata or {}),
            },
            note=reason,
            timestamp=timestamp,
        )

    def recover(
        self,
        actor: str,
        *,
        proposal: Mapping[str, object] | None = None,
        note: str | None = None,
    ) -> NegotiationEvent:
        self._assert_party(actor)
        if self._state is not NegotiationPhase.FAILED:
            raise InvalidTransitionError("No recoverable failure is active")

        last_failure = self._failures[-1] if self._failures else None
        if not last_failure or not last_failure.recoverable:
            raise RecoveryError("Last failure is not recoverable")

        timestamp = self._clock()
        event = self._record_event(
            actor,
            NegotiationPhase.RECOVERED,
            payload={"reason": last_failure.reason},
            note=note or last_failure.reason,
            timestamp=timestamp,
        )
        self._state = NegotiationPhase.RECOVERED
        self._closed = False
        self._recovery_attempts += 1

        if proposal is not None:
            self.propose(actor, proposal, note=note)
        else:
            self._active_offer = None
        return event

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _assert_party(self, actor: str) -> None:
        if actor not in self._party_set:
            raise UnauthorizedPartyError(f"Unknown negotiation actor: {actor}")

    def _ensure_open(self) -> None:
        if self._closed:
            raise InvalidTransitionError("Negotiation session is closed")

    def _record_event(
        self,
        actor: str,
        phase: NegotiationPhase,
        *,
        payload: Mapping[str, object] | None = None,
        note: str | None = None,
        timestamp: datetime | None = None,
    ) -> NegotiationEvent:
        event = NegotiationEvent(
            timestamp=timestamp or self._clock(),
            actor=actor,
            phase=phase,
            payload=dict(payload or {}),
            note=note,
        )
        self._history.append(event)
        return event

    def _register_failure(
        self,
        actor: str,
        reason: str,
        *,
        recoverable: bool,
        metadata: Mapping[str, object],
        timestamp: datetime,
    ) -> FailureRecord:
        record = FailureRecord(
            timestamp=timestamp,
            actor=actor,
            reason=reason,
            recoverable=recoverable,
            metadata=dict(metadata),
        )
        self._failures.append(record)
        return record


def replay_events(events: Iterable[NegotiationEvent]) -> list[Dict[str, object]]:
    """Return serialised dictionaries for ``events`` preserving order."""

    return [event.as_dict() for event in events]
