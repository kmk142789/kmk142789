"""Retention policy utilities for ethical telemetry governance."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .schema import ConsentState, TelemetryEvent
from .storage import TelemetryStorage

__all__ = [
    "RemovedTelemetryEvent",
    "RetentionDecision",
    "RetentionPolicy",
    "enforce_retention_policy",
    "EXPIRED_REASON",
    "CONSENT_OPT_OUT_REASON",
    "CONSENT_UNKNOWN_REASON",
]


EXPIRED_REASON = "expired"
CONSENT_OPT_OUT_REASON = "consent-opt-out"
CONSENT_UNKNOWN_REASON = "consent-unknown"


@dataclass(frozen=True)
class RemovedTelemetryEvent:
    """Record describing an event removed by a retention policy."""

    event: TelemetryEvent
    reason: str


@dataclass(frozen=True)
class RetentionDecision:
    """Result of evaluating telemetry events against a retention policy."""

    retained: tuple[TelemetryEvent, ...]
    removed: tuple[RemovedTelemetryEvent, ...]
    reference_time: datetime
    cutoff: datetime | None

    @property
    def retained_count(self) -> int:
        return len(self.retained)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def removed_reason_counts(self) -> dict[str, int]:
        """Return a breakdown of removal reasons."""

        counts: Counter[str] = Counter(record.reason for record in self.removed)
        return dict(counts)

    def removed_for_reason(self, reason: str) -> tuple[TelemetryEvent, ...]:
        """Return events removed for a specific reason."""

        return tuple(record.event for record in self.removed if record.reason == reason)


@dataclass(frozen=True)
class RetentionPolicy:
    """Governance rules defining how long telemetry events may be retained."""

    max_event_age: timedelta | None
    allow_unknown_consent: bool = False
    allow_opted_out_events: bool = False

    def __post_init__(self) -> None:
        if self.max_event_age is not None and self.max_event_age <= timedelta(0):
            raise ValueError("max_event_age must be a positive duration or None")

    def evaluate(
        self,
        events: Iterable[TelemetryEvent],
        *,
        reference_time: datetime | None = None,
    ) -> RetentionDecision:
        """Evaluate events against the policy returning retained and removed sets."""

        snapshot_time = _normalise_reference_time(reference_time)
        cutoff = snapshot_time - self.max_event_age if self.max_event_age is not None else None

        retained: list[TelemetryEvent] = []
        removed: list[RemovedTelemetryEvent] = []

        for event in events:
            reason = self._retention_reason(event, cutoff)
            if reason is None:
                retained.append(event)
            else:
                removed.append(RemovedTelemetryEvent(event=event, reason=reason))

        return RetentionDecision(
            retained=tuple(retained),
            removed=tuple(removed),
            reference_time=snapshot_time,
            cutoff=cutoff,
        )

    def _retention_reason(
        self, event: TelemetryEvent, cutoff: datetime | None
    ) -> str | None:
        consent_state = event.context.consent_state
        if consent_state is ConsentState.OPTED_OUT and not self.allow_opted_out_events:
            return CONSENT_OPT_OUT_REASON
        if (
            consent_state is ConsentState.UNKNOWN
            and not self.allow_unknown_consent
        ):
            return CONSENT_UNKNOWN_REASON
        if cutoff is not None and event.occurred_at < cutoff:
            return EXPIRED_REASON
        return None


def _normalise_reference_time(reference_time: datetime | None) -> datetime:
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    else:
        reference_time = reference_time.astimezone(timezone.utc)
    return reference_time


def enforce_retention_policy(
    storage: TelemetryStorage,
    policy: RetentionPolicy,
    *,
    reference_time: datetime | None = None,
) -> RetentionDecision:
    """Apply a retention policy to a storage backend and persist the result."""

    events = list(storage.read())
    decision = policy.evaluate(events, reference_time=reference_time)
    if decision.removed:
        storage.replace(decision.retained)
        storage.flush()
    return decision
