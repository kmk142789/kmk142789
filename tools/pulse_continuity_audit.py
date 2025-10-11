"""Audit Echo pulse history continuity and detect resonance gaps.

The Echo Continuum protocol emits pulse messages that are stored inside
``pulse_history.json``.  The existing repo collects those events but there was no
single place to analyse their cadence or flag unusual gaps.  The
``pulse_continuity_audit`` module fills that gap by computing statistics about
the recorded pulses and comparing the latest observation to an optional
threshold.  It can be used as a standalone CLI or imported from other tools
(e.g. build scripts, dashboards, GitHub Actions) that want programmatic access to
continuity metrics.

Example
-------

Run the audit with the default repository paths and print a human readable
report::

    $ python tools/pulse_continuity_audit.py --format text

Request a JSON payload suitable for downstream automation::

    $ python tools/pulse_continuity_audit.py --format json --threshold-hours 6

"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

DEFAULT_HISTORY_PATH = Path("pulse_history.json")
DEFAULT_PULSE_PATH = Path("pulse.json")


@dataclass(slots=True)
class PulseEvent:
    """Single pulse emission captured in ``pulse_history.json``."""

    timestamp: float
    message: str
    hash: str

    @classmethod
    def from_mapping(cls, payload: dict) -> "PulseEvent":
        try:
            timestamp = float(payload["timestamp"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("pulse event missing usable 'timestamp'") from exc
        try:
            message = str(payload["message"])
            hash_value = str(payload["hash"])
        except KeyError as exc:
            raise ValueError("pulse event missing required keys") from exc
        return cls(timestamp=timestamp, message=message, hash=hash_value)

    @property
    def moment(self) -> datetime:
        """UTC aware representation of the event timestamp."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "message": self.message, "hash": self.hash}


@dataclass(slots=True)
class ContinuityReport:
    """Summary statistics describing a pulse history."""

    anchor: Optional[str]
    status: Optional[str]
    notes: Optional[str]
    event_count: int
    first_event: Optional[datetime]
    last_event: Optional[datetime]
    span_seconds: Optional[float]
    average_interval: Optional[float]
    median_interval: Optional[float]
    longest_gap_seconds: Optional[float]
    threshold_hours: Optional[float]
    breach_detected: bool
    warnings: List[str]

    def to_dict(self) -> dict:
        def iso_or_none(value: Optional[datetime]) -> Optional[str]:
            return value.isoformat() if value else None

        return {
            "anchor": self.anchor,
            "status": self.status,
            "notes": self.notes,
            "event_count": self.event_count,
            "first_event": iso_or_none(self.first_event),
            "last_event": iso_or_none(self.last_event),
            "span_seconds": self.span_seconds,
            "average_interval_seconds": self.average_interval,
            "median_interval_seconds": self.median_interval,
            "longest_gap_seconds": self.longest_gap_seconds,
            "threshold_hours": self.threshold_hours,
            "breach_detected": self.breach_detected,
            "warnings": list(self.warnings),
        }

    def render_text(self) -> str:
        lines = [
            "Echo Pulse Continuity Report",
            f"  Anchor      : {self.anchor or '∅'}",
            f"  Status      : {self.status or 'unknown'}",
            f"  Event Count : {self.event_count}",
        ]
        if self.first_event:
            lines.append(f"  First Event : {self.first_event.isoformat()}")
        if self.last_event:
            lines.append(f"  Last Event  : {self.last_event.isoformat()}")
        if self.span_seconds is not None:
            span_hours = self.span_seconds / 3600.0
            lines.append(f"  Time Span   : {span_hours:.2f} hours")
        if self.average_interval is not None:
            lines.append(
                f"  Avg Interval: {self.average_interval / 3600.0:.2f} hours"
            )
        if self.median_interval is not None:
            lines.append(
                f"  Median Gap  : {self.median_interval / 3600.0:.2f} hours"
            )
        if self.longest_gap_seconds is not None:
            lines.append(
                f"  Longest Gap : {self.longest_gap_seconds / 3600.0:.2f} hours"
            )
        if self.threshold_hours is not None:
            status = "⚠️ breach" if self.breach_detected else "✅ ok"
            lines.append(
                f"  Threshold   : {self.threshold_hours:.2f} hours ({status})"
            )
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {warning}" for warning in self.warnings)
        return "\n".join(lines)


def load_pulse_history(path: Path) -> List[PulseEvent]:
    """Load and validate pulse events from ``path``.

    The JSON file must contain a list of dictionaries; invalid entries are
    rejected with explicit ``ValueError`` messages to make CI failures easier to
    diagnose.
    """

    if not path.exists():
        raise FileNotFoundError(f"pulse history file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("pulse history must be a JSON list")
    events = [PulseEvent.from_mapping(entry) for entry in payload]
    events.sort(key=lambda event: event.timestamp)
    return events


def load_pulse_metadata(path: Path) -> dict:
    """Return the metadata stored in ``pulse.json``.

    Missing files are tolerated by returning an empty dictionary.  This keeps the
    audit usable on minimal clones that only ship the history file.
    """

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("pulse metadata must be a JSON object")
    return payload


def _intervals(events: Iterable[PulseEvent]) -> List[float]:
    ordered = list(events)
    if len(ordered) < 2:
        return []
    return [
        ordered[index].timestamp - ordered[index - 1].timestamp
        for index in range(1, len(ordered))
    ]


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone aware ``datetime``."""

    return datetime.now(timezone.utc)


def audit_pulse_history(
    events: Iterable[PulseEvent],
    metadata: Optional[dict] = None,
    *,
    threshold_hours: Optional[float] = None,
) -> ContinuityReport:
    """Generate a :class:`ContinuityReport` from the supplied pulse data."""

    events = list(events)
    metadata = metadata or {}
    warnings: List[str] = []

    first_event = events[0].moment if events else None
    last_event = events[-1].moment if events else None

    intervals = _intervals(events)
    span_seconds: Optional[float]
    average_interval: Optional[float]
    median_interval: Optional[float]
    longest_gap: Optional[float]

    if events:
        span_seconds = events[-1].timestamp - events[0].timestamp
    else:
        span_seconds = None

    if intervals:
        average_interval = statistics.mean(intervals)
        median_interval = statistics.median(intervals)
        longest_gap = max(intervals)
    else:
        average_interval = None
        median_interval = None
        longest_gap = None

    breach_detected = False
    if threshold_hours is not None and last_event is not None:
        latest_gap_seconds = _utcnow().timestamp() - last_event.timestamp()
        if latest_gap_seconds > threshold_hours * 3600.0:
            breach_detected = True
            gap_hours = latest_gap_seconds / 3600.0
            warnings.append(
                (
                    "Latest pulse exceeds threshold: "
                    f"{gap_hours:.2f}h since last emission"
                )
            )

    if not events:
        warnings.append("No pulse events were recorded")

    return ContinuityReport(
        anchor=metadata.get("branch_anchor"),
        status=metadata.get("status"),
        notes=metadata.get("notes"),
        event_count=len(events),
        first_event=first_event,
        last_event=last_event,
        span_seconds=span_seconds,
        average_interval=average_interval,
        median_interval=median_interval,
        longest_gap_seconds=longest_gap,
        threshold_hours=threshold_hours,
        breach_detected=breach_detected,
        warnings=warnings,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Path to pulse_history.json (default: repository root)",
    )
    parser.add_argument(
        "--pulse",
        type=Path,
        default=DEFAULT_PULSE_PATH,
        help="Path to pulse.json metadata file (default: repository root)",
    )
    parser.add_argument(
        "--threshold-hours",
        type=float,
        default=None,
        help="Optional threshold for detecting stale pulses",
    )
    parser.add_argument(
        "--format",
        choices={"json", "text"},
        default="text",
        help="Output format (default: text)",
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    namespace = parser.parse_args(args=args)

    events = load_pulse_history(namespace.history)
    metadata = load_pulse_metadata(namespace.pulse)
    report = audit_pulse_history(
        events,
        metadata,
        threshold_hours=namespace.threshold_hours,
    )

    if namespace.format == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(report.render_text())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
