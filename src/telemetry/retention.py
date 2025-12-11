"""Retention policy utilities for ethical telemetry governance."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .schema import ConsentState, TelemetryEvent
from .storage import JsonlTelemetryStorage, TelemetryStorage

__all__ = [
    "RemovedTelemetryEvent",
    "RetentionDecision",
    "RetentionPolicy",
    "enforce_retention_policy",
    "EXPIRED_REASON",
    "CONSENT_OPT_OUT_REASON",
    "CONSENT_UNKNOWN_REASON",
    "main",
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

    def as_dict(self) -> dict[str, object]:
        """Serialise the retention outcome to a JSON-friendly mapping."""

        return {
            "retained_count": self.retained_count,
            "removed_count": self.removed_count,
            "removed_reason_counts": self.removed_reason_counts,
            "reference_time": _datetime_to_iso(self.reference_time),
            "cutoff": _datetime_to_iso(self.cutoff),
        }

    def describe(self) -> str:
        """Render a human-readable summary of the retention sweep."""

        lines = [
            f"Retained events: {self.retained_count}",
            f"Removed events: {self.removed_count}",
            f"Reference time: {_datetime_to_iso(self.reference_time)}",
        ]
        if self.cutoff is not None:
            lines.append(f"Cutoff: {_datetime_to_iso(self.cutoff)}")
        if self.removed_reason_counts:
            lines.append("Removal breakdown:")
            for reason, count in sorted(
                self.removed_reason_counts.items(), key=lambda item: item[1], reverse=True
            ):
                lines.append(f"  - {reason}: {count}")
        return "\n".join(lines)


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


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply ethical telemetry retention rules to a JSONL log file.",
    )
    parser.add_argument("path", type=Path, help="Path to the telemetry JSONL log file.")

    age_group = parser.add_mutually_exclusive_group()
    age_group.add_argument(
        "--max-age-days",
        type=float,
        default=30.0,
        help="Number of days to retain events before expiration (default: 30).",
    )
    age_group.add_argument(
        "--no-age-limit",
        action="store_true",
        help="Disable age-based retention and only enforce consent rules.",
    )

    parser.add_argument(
        "--allow-unknown-consent",
        action="store_true",
        help="Keep events where consent is unknown instead of removing them.",
    )
    parser.add_argument(
        "--allow-opted-out-events",
        action="store_true",
        help="Retain events produced when users opted out of telemetry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate the policy without persisting removals.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the decision as formatted JSON instead of human-readable text.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _resolve_policy(args: argparse.Namespace) -> RetentionPolicy:
    if args.no_age_limit:
        max_age = None
    else:
        if args.max_age_days is not None and args.max_age_days <= 0:
            raise ValueError("max-age-days must be greater than zero when provided")
        max_age = None if args.max_age_days is None else timedelta(days=args.max_age_days)

    return RetentionPolicy(
        max_event_age=max_age,
        allow_unknown_consent=args.allow_unknown_consent,
        allow_opted_out_events=args.allow_opted_out_events,
    )


def _render_decision(decision: RetentionDecision, *, json_output: bool) -> None:
    if json_output:
        json.dump(decision.as_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(decision.describe())


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for enforcing retention rules from the command line."""

    args = _parse_args(argv)
    try:
        policy = _resolve_policy(args)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    reference_time = datetime.now(timezone.utc)
    storage = JsonlTelemetryStorage(args.path)

    if args.dry_run:
        events = list(storage.read())
        decision = policy.evaluate(events, reference_time=reference_time)
    else:
        decision = enforce_retention_policy(
            storage, policy, reference_time=reference_time
        )

    _render_decision(decision, json_output=args.json)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    raise SystemExit(main())
