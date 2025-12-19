"""Resilience pulse reporting for telemetry pipelines."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import TelemetryEvent
from .storage import JsonlTelemetryStorage

__all__ = [
    "ResiliencePulseReport",
    "ResiliencePulseError",
    "generate_resilience_report",
    "main",
]


class ResiliencePulseError(RuntimeError):
    """Raised when a resilience pulse report cannot be produced."""


@dataclass(frozen=True)
class ResiliencePulseReport:
    """Summary of operational resilience derived from telemetry events."""

    total_events: int
    window_minutes: float
    events_per_minute: float
    longest_gap_minutes: float | None
    anomaly_events: int
    critical_sessions: int
    resilience_score: float
    first_event_at: datetime | None
    last_event_at: datetime | None
    recommendations: list[str]

    def as_dict(self) -> dict[str, Any]:
        """Serialise the resilience report to a JSON compatible mapping."""

        payload: dict[str, Any] = {
            "total_events": self.total_events,
            "window_minutes": self.window_minutes,
            "events_per_minute": self.events_per_minute,
            "longest_gap_minutes": self.longest_gap_minutes,
            "anomaly_events": self.anomaly_events,
            "critical_sessions": self.critical_sessions,
            "resilience_score": self.resilience_score,
            "recommendations": self.recommendations,
        }
        payload["first_event_at"] = _datetime_to_iso(self.first_event_at)
        payload["last_event_at"] = _datetime_to_iso(self.last_event_at)
        return payload

    def describe(self) -> str:
        """Render a human readable view of the resilience summary."""

        lines = [
            f"Total events: {self.total_events}",
            f"Observation window: {self.window_minutes:.1f} minutes",
            f"Events per minute: {self.events_per_minute:.2f}",
            f"Anomaly events: {self.anomaly_events}",
            f"Critical sessions: {self.critical_sessions}",
            f"Resilience score: {self.resilience_score:.2f}",
        ]
        if self.first_event_at is not None:
            lines.append(f"First event: {_datetime_to_iso(self.first_event_at)}")
        if self.last_event_at is not None:
            lines.append(f"Last event: {_datetime_to_iso(self.last_event_at)}")
        if self.longest_gap_minutes is not None:
            lines.append(f"Longest gap: {self.longest_gap_minutes:.1f} minutes")
        if self.recommendations:
            lines.append("Recommendations:")
            lines.extend(f"  - {item}" for item in self.recommendations)
        return "\n".join(lines)


def generate_resilience_report(
    path: Path, *, now: datetime | None = None
) -> ResiliencePulseReport:
    """Generate a :class:`ResiliencePulseReport` from a JSONL telemetry log."""

    if not path.exists():
        raise ResiliencePulseError(f"telemetry log not found: {path}")

    storage = JsonlTelemetryStorage(path)
    events = list(storage.read())

    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if not events:
        return _empty_report(now)

    sorted_events = sorted(events, key=lambda event: event.occurred_at)
    timestamps = [_normalize_datetime(event.occurred_at) for event in sorted_events]

    first_event_at = timestamps[0]
    last_event_at = timestamps[-1]
    window_minutes = max((last_event_at - first_event_at).total_seconds() / 60.0, 0.0)
    window_minutes = max(window_minutes, 1.0)

    anomaly_events = sum(1 for event in sorted_events if _is_anomaly(event))
    critical_sessions = _count_critical_sessions(sorted_events)
    longest_gap = _longest_gap_minutes(timestamps)
    events_per_minute = len(events) / window_minutes

    resilience_score = _compute_resilience_score(
        window_minutes=window_minutes,
        longest_gap_minutes=longest_gap,
        anomaly_events=anomaly_events,
        total_events=len(events),
    )
    recommendations = _build_recommendations(
        window_minutes=window_minutes,
        longest_gap_minutes=longest_gap,
        anomaly_events=anomaly_events,
        total_events=len(events),
        critical_sessions=critical_sessions,
    )

    return ResiliencePulseReport(
        total_events=len(events),
        window_minutes=round(window_minutes, 2),
        events_per_minute=round(events_per_minute, 4),
        longest_gap_minutes=round(longest_gap, 2) if longest_gap is not None else None,
        anomaly_events=anomaly_events,
        critical_sessions=critical_sessions,
        resilience_score=round(resilience_score, 3),
        first_event_at=first_event_at,
        last_event_at=last_event_at,
        recommendations=recommendations,
    )


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for the resilience pulse report CLI."""

    parser = argparse.ArgumentParser(
        description="Analyse telemetry JSONL artefacts for operational resilience signals."
    )
    parser.add_argument("path", type=Path, help="Path to the telemetry JSONL log file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as formatted JSON instead of human readable text.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = generate_resilience_report(args.path)
    except ResiliencePulseError as exc:
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


def _is_anomaly(event: TelemetryEvent) -> bool:
    event_type = event.event_type.lower()
    payload = event.payload

    if "error" in event_type or "failure" in event_type:
        return True
    if _payload_flag(payload, "anomaly"):
        return True

    severity = _payload_text(payload, "severity")
    if severity in {"high", "critical", "severe"}:
        return True

    status = _payload_text(payload, "status")
    if status in {"fail", "failed", "failure", "degraded"}:
        return True

    return False


def _payload_text(payload: Mapping[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    value = payload.get(key)
    if value is None:
        return None
    return str(value).strip().lower()


def _payload_flag(payload: Mapping[str, Any], key: str) -> bool:
    if key not in payload:
        return False
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    return str(value).strip().lower() in {"1", "true", "yes"}


def _count_critical_sessions(events: list[TelemetryEvent]) -> int:
    session_anomalies: dict[str, int] = {}
    for event in events:
        if not _is_anomaly(event):
            continue
        session_key = event.context.session_label or event.context.pseudonymous_id
        session_anomalies[session_key] = session_anomalies.get(session_key, 0) + 1
    return sum(1 for count in session_anomalies.values() if count >= 3)


def _longest_gap_minutes(timestamps: list[datetime]) -> float | None:
    if len(timestamps) < 2:
        return 0.0
    gaps = []
    for earlier, later in zip(timestamps, timestamps[1:]):
        gap = max((later - earlier).total_seconds() / 60.0, 0.0)
        gaps.append(gap)
    return max(gaps) if gaps else None


def _compute_resilience_score(
    *,
    window_minutes: float,
    longest_gap_minutes: float | None,
    anomaly_events: int,
    total_events: int,
) -> float:
    if total_events == 0:
        return 0.0
    longest_gap_minutes = longest_gap_minutes or 0.0
    availability_score = 1 - min(1.0, longest_gap_minutes / max(window_minutes, 1.0))
    anomaly_rate = anomaly_events / max(total_events, 1)
    anomaly_penalty = min(0.6, anomaly_rate * 1.5)
    return max(0.0, min(1.0, availability_score - anomaly_penalty))


def _build_recommendations(
    *,
    window_minutes: float,
    longest_gap_minutes: float | None,
    anomaly_events: int,
    total_events: int,
    critical_sessions: int,
) -> list[str]:
    recommendations: list[str] = []
    anomaly_rate = anomaly_events / max(total_events, 1)
    if anomaly_rate >= 0.2:
        recommendations.append("Investigate error-heavy channels to reduce anomaly rates.")
    if longest_gap_minutes is not None and longest_gap_minutes >= max(30.0, window_minutes * 0.25):
        recommendations.append("Reduce telemetry gaps by improving collection cadence.")
    if critical_sessions:
        recommendations.append("Stabilize sessions with repeated anomalies to improve continuity.")
    if not recommendations:
        recommendations.append("Maintain current telemetry posture and continue monitoring.")
    return recommendations


def _empty_report(now: datetime) -> ResiliencePulseReport:
    return ResiliencePulseReport(
        total_events=0,
        window_minutes=0.0,
        events_per_minute=0.0,
        longest_gap_minutes=None,
        anomaly_events=0,
        critical_sessions=0,
        resilience_score=0.0,
        first_event_at=None,
        last_event_at=None,
        recommendations=["No telemetry events observed; verify the pipeline is active."],
    )
