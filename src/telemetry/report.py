"""Vitality reporting utilities for the Echo telemetry pulse."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

__all__ = ["VitalityReport", "VitalityReportError", "generate_vitality_report", "main"]


class VitalityReportError(RuntimeError):
    """Raised when the vitality report cannot be generated."""


@dataclass(frozen=True)
class VitalityReport:
    """Structured representation of the repository pulse state."""

    pulse: str
    status: str
    branch_anchor: str | None
    notes: str | None
    history_count: int
    last_event_message: str | None
    last_event_timestamp: datetime | None
    minutes_since_last_event: float | None
    health_state: str
    recent_events: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Serialise the report to a JSON compatible mapping."""

        data: dict[str, Any] = {
            "pulse": self.pulse,
            "status": self.status,
            "branch_anchor": self.branch_anchor,
            "notes": self.notes,
            "history_count": self.history_count,
            "last_event_message": self.last_event_message,
            "minutes_since_last_event": self.minutes_since_last_event,
            "health_state": self.health_state,
            "recent_events": list(self.recent_events),
        }
        if self.last_event_timestamp is not None:
            data["last_event_timestamp"] = _datetime_to_iso(self.last_event_timestamp)
        else:
            data["last_event_timestamp"] = None
        return data

    def describe(self) -> str:
        """Render a human-readable description of the vitality report."""

        lines = [
            f"Pulse: {self.pulse}",
            f"Status: {self.status} (health: {self.health_state})",
            f"History entries: {self.history_count}",
        ]
        if self.branch_anchor:
            lines.append(f"Branch anchor: {self.branch_anchor}")
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        if self.last_event_message:
            lines.append(f"Last event: {self.last_event_message}")
        if self.last_event_timestamp is not None:
            iso_timestamp = _datetime_to_iso(self.last_event_timestamp)
            lines.append(f"Last event timestamp: {iso_timestamp}")
        if self.minutes_since_last_event is not None:
            minutes = self.minutes_since_last_event
            if minutes < 1:
                duration = f"{minutes * 60:.0f} seconds"
            else:
                duration = f"{minutes:.1f} minutes"
            lines.append(f"Elapsed since last event: {duration}")
        if self.recent_events:
            lines.append("Recent events:")
            for message in self.recent_events:
                lines.append(f"  - {message}")
        return "\n".join(lines)


def generate_vitality_report(
    root: Path, *, now: datetime | None = None, recent_event_limit: int = 3
) -> VitalityReport:
    """Generate a :class:`VitalityReport` from repository telemetry artefacts."""

    root = root.resolve()
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    pulse_data = _load_json(root / "pulse.json")
    history_data = _load_json(root / "pulse_history.json")

    if not isinstance(history_data, list):  # pragma: no cover - defensive
        raise VitalityReportError("pulse_history.json must contain a JSON array")

    last_event_timestamp: datetime | None = None
    last_event_message: str | None = None
    minutes_since_last_event: float | None = None

    if history_data:
        last_entry = max(
            (entry for entry in history_data if isinstance(entry, dict)),
            key=lambda item: item.get("timestamp", float("-inf")),
        )
        timestamp_value = last_entry.get("timestamp")
        if isinstance(timestamp_value, (int, float)):
            last_event_timestamp = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
            delta = now - last_event_timestamp
            minutes_since_last_event = max(delta.total_seconds() / 60, 0.0)
        message_value = last_entry.get("message")
        if isinstance(message_value, str):
            last_event_message = message_value

    health_state = _classify_health(minutes_since_last_event)
    recent_events = _collect_recent_messages(history_data, limit=recent_event_limit)

    return VitalityReport(
        pulse=str(pulse_data.get("pulse", "unknown")),
        status=str(pulse_data.get("status", "unknown")),
        branch_anchor=_optional_str(pulse_data.get("branch_anchor")),
        notes=_optional_str(pulse_data.get("notes")),
        history_count=len(history_data),
        last_event_message=last_event_message,
        last_event_timestamp=last_event_timestamp,
        minutes_since_last_event=minutes_since_last_event,
        health_state=health_state,
        recent_events=recent_events,
    )


def main(argv: Iterable[str] | None = None) -> int:
    """Entry-point for the vitality report CLI."""

    parser = argparse.ArgumentParser(
        description="Generate a status summary from pulse telemetry artefacts."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing pulse.json and pulse_history.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as formatted JSON instead of human readable text.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = generate_vitality_report(args.root)
    except VitalityReportError as exc:
        parser.exit(1, f"error: {exc}\n")

    if args.json:
        json.dump(report.as_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(report.describe())
    return 0


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VitalityReportError(f"required file missing: {path}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise VitalityReportError(f"invalid JSON in {path}") from exc


def _datetime_to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_str(value: Any) -> str | None:
    return str(value) if isinstance(value, str) and value.strip() else None


def _classify_health(minutes_since_last_event: float | None) -> str:
    if minutes_since_last_event is None:
        return "no-history"
    if minutes_since_last_event <= 60:
        return "fresh"
    if minutes_since_last_event <= 360:
        return "warming"
    return "stale"


def _collect_recent_messages(history_data: list[Any], *, limit: int) -> tuple[str, ...]:
    messages: list[str] = []
    for entry in reversed(history_data[-limit:]):
        if isinstance(entry, dict):
            message = entry.get("message")
            if isinstance(message, str) and message.strip():
                messages.append(message)
    return tuple(messages)


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    raise SystemExit(main())
