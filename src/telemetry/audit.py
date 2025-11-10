"""Telemetry consent compliance auditing utilities."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import ConsentState
from .storage import JsonlTelemetryStorage

__all__ = [
    "ConsentComplianceError",
    "ConsentComplianceReport",
    "generate_compliance_report",
    "main",
]


class ConsentComplianceError(RuntimeError):
    """Raised when a consent compliance report cannot be produced."""


@dataclass(frozen=True)
class ConsentComplianceReport:
    """Summary of consent and session activity derived from telemetry events."""

    total_events: int
    consent_counts: Mapping[str, int]
    event_type_counts: Mapping[str, int]
    unique_sessions: int
    first_event_at: datetime | None
    last_event_at: datetime | None
    minutes_active: float | None
    minutes_since_last_event: float | None
    non_opt_in_events: int

    def as_dict(self) -> dict[str, Any]:
        """Serialise the compliance report to a JSON compatible mapping."""

        payload: dict[str, Any] = {
            "total_events": self.total_events,
            "consent_counts": dict(self.consent_counts),
            "event_type_counts": dict(self.event_type_counts),
            "unique_sessions": self.unique_sessions,
            "minutes_active": self.minutes_active,
            "minutes_since_last_event": self.minutes_since_last_event,
            "non_opt_in_events": self.non_opt_in_events,
        }
        payload["first_event_at"] = _datetime_to_iso(self.first_event_at)
        payload["last_event_at"] = _datetime_to_iso(self.last_event_at)
        return payload

    def describe(self) -> str:
        """Render a human readable view of the consent compliance summary."""

        lines = [
            f"Total events: {self.total_events}",
            f"Unique sessions: {self.unique_sessions}",
        ]
        if self.minutes_active is not None:
            if self.minutes_active < 1:
                duration = f"{self.minutes_active * 60:.0f} seconds"
            else:
                duration = f"{self.minutes_active:.1f} minutes"
            lines.append(f"Observation window: {duration}")
        if self.first_event_at is not None:
            lines.append(f"First event: {_datetime_to_iso(self.first_event_at)}")
        if self.last_event_at is not None:
            lines.append(f"Last event: {_datetime_to_iso(self.last_event_at)}")
        if self.minutes_since_last_event is not None:
            if self.minutes_since_last_event < 1:
                elapsed = f"{self.minutes_since_last_event * 60:.0f} seconds"
            else:
                elapsed = f"{self.minutes_since_last_event:.1f} minutes"
            lines.append(f"Elapsed since last event: {elapsed}")

        if self.consent_counts:
            lines.append("Consent distribution:")
            for state, count in sorted(
                self.consent_counts.items(), key=lambda item: item[1], reverse=True
            ):
                lines.append(f"  - {state}: {count}")
        if self.non_opt_in_events:
            lines.append(
                f"⚠️ Events recorded without opt-in consent: {self.non_opt_in_events}"
            )

        if self.event_type_counts:
            lines.append("Event type counts:")
            for event_type, count in sorted(
                self.event_type_counts.items(), key=lambda item: item[1], reverse=True
            ):
                lines.append(f"  - {event_type}: {count}")
        return "\n".join(lines)


def generate_compliance_report(
    path: Path, *, now: datetime | None = None
) -> ConsentComplianceReport:
    """Generate a :class:`ConsentComplianceReport` from a JSONL telemetry log."""

    if not path.exists():
        raise ConsentComplianceError(f"telemetry log not found: {path}")

    storage = JsonlTelemetryStorage(path)
    events = list(storage.read())

    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    consent_counter: Counter[str] = Counter()
    event_type_counter: Counter[str] = Counter()
    session_ids: set[str] = set()
    first_event_at: datetime | None = None
    last_event_at: datetime | None = None
    non_opt_in_events = 0

    for event in events:
        consent = event.consent_snapshot or event.context.consent_state
        consent_label = consent.value if isinstance(consent, ConsentState) else str(consent)
        consent_counter[consent_label] += 1
        if isinstance(consent, ConsentState) and not consent.allows_collection:
            non_opt_in_events += 1

        event_type_counter[event.event_type] += 1
        session_ids.add(event.context.pseudonymous_id)

        occurred_at = _normalize_datetime(event.occurred_at)
        if first_event_at is None or occurred_at < first_event_at:
            first_event_at = occurred_at
        if last_event_at is None or occurred_at > last_event_at:
            last_event_at = occurred_at

    minutes_active = None
    minutes_since_last_event = None
    if first_event_at and last_event_at:
        minutes_active = max((last_event_at - first_event_at).total_seconds() / 60.0, 0.0)
        minutes_since_last_event = max((now - last_event_at).total_seconds() / 60.0, 0.0)

    return ConsentComplianceReport(
        total_events=len(events),
        consent_counts=dict(consent_counter),
        event_type_counts=dict(event_type_counter),
        unique_sessions=len(session_ids),
        first_event_at=first_event_at,
        last_event_at=last_event_at,
        minutes_active=minutes_active,
        minutes_since_last_event=minutes_since_last_event,
        non_opt_in_events=non_opt_in_events,
    )


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for the consent compliance report CLI."""

    parser = argparse.ArgumentParser(
        description="Analyse telemetry JSONL artefacts for consent compliance insights."
    )
    parser.add_argument("path", type=Path, help="Path to the telemetry JSONL log file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as formatted JSON instead of human readable text.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = generate_compliance_report(args.path)
    except ConsentComplianceError as exc:
        parser.exit(1, f"error: {exc}\n")

    if args.json:
        json.dump(report.as_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(report.describe())
    return 0


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    value = _normalize_datetime(value)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    raise SystemExit(main())
