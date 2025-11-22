"""Storyboard the pulse history into narrative sessions.

The standard pulse history ledger records every evolution ping with timestamped messages.
While raw tables and tempo summaries exist, this storyboarder groups pulses into
"sessions" – bursts of activity separated by configurable idle gaps – and renders them as
human-friendly narrative beats.  The aim is to quickly answer:

* When was the last creative sprint?
* How dense was each sprint compared to the others?
* Which sources (manual pushes, automations, experiments) were most active per session?

The module exposes pure functions for easy unit testing and a compact CLI for interactive
use.  By default the CLI reads ``pulse_history.json`` from the current directory and
prints a text storyboard; pass ``--json`` to retrieve structured data instead.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

from echo_pulse_novum import PulseEvent, load_pulse_history


@dataclass(slots=True)
class PulseSession:
    """Bundle of pulse events that belong to the same activity window."""

    events: List[PulseEvent]

    @property
    def start(self) -> datetime:
        return self.events[0].moment

    @property
    def end(self) -> datetime:
        return self.events[-1].moment

    @property
    def sources(self) -> Counter[str]:
        return Counter(source_from_message(event.message) for event in self.events)

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds() or 1.0

    @property
    def cadence_per_hour(self) -> float:
        return (len(self.events) / self.duration_seconds) * 3600


def source_from_message(message: str) -> str:
    """Extract the source channel from a pulse message.

    The pulse messages follow the pattern ``"<emoji> evolve:<source>:<id>"``.
    When no clear source is found, the function returns ``"unknown"`` so callers
    do not need to guard against missing data.
    """

    parts = message.split(":")
    if len(parts) >= 2:
        return parts[1].strip() or "unknown"
    return "unknown"


def segment_sessions(
    events: Sequence[PulseEvent], *, max_gap_seconds: float = 1800.0
) -> List[PulseSession]:
    """Group events into sessions separated by gaps greater than ``max_gap_seconds``."""

    if not events:
        return []

    sessions: List[PulseSession] = []
    current: List[PulseEvent] = []

    for event in sorted(events, key=lambda item: item.timestamp):
        if current and (event.timestamp - current[-1].timestamp) > max_gap_seconds:
            sessions.append(PulseSession(events=list(current)))
            current.clear()
        current.append(event)

    if current:
        sessions.append(PulseSession(events=current))

    return sessions


def _format_sources(counter: Counter[str]) -> str:
    top = counter.most_common()
    if not top:
        return "unknown"
    return ", ".join(f"{source}×{count}" for source, count in top)


def _format_span(start: datetime, end: datetime) -> str:
    duration = end - start
    minutes = duration.total_seconds() / 60
    if minutes < 1:
        return "<1m"
    if minutes < 60:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


def build_storyboard(sessions: Sequence[PulseSession]) -> str:
    """Render a human-readable storyboard of the provided sessions."""

    if not sessions:
        return "No pulse sessions found. Launch a cycle to start the story."

    total_events = sum(len(session.events) for session in sessions)
    lines = [
        "Pulse Storyboard",
        "================",
        f"Sessions discovered : {len(sessions)}",
        f"Events total        : {total_events}",
        "",
    ]

    for index, session in enumerate(sessions, start=1):
        span = _format_span(session.start, session.end)
        sources = _format_sources(session.sources)
        lines.extend(
            [
                f"Session {index}: {session.start.isoformat()} → {session.end.isoformat()}",
                f"  Span        : {span}",
                f"  Events      : {len(session.events)}",
                f"  Sources     : {sources}",
                f"  Cadence     : {session.cadence_per_hour:.2f} events/hour",
            ]
        )
        latest = session.events[-1]
        lines.append(f"  Latest note : {latest.message} ({latest.hash[:8]}…)")
        if index != len(sessions):
            lines.append("")

    return "\n".join(lines)


def storyboard_as_dict(sessions: Sequence[PulseSession]) -> dict:
    """Convert the storyboard into a structured dictionary for JSON output."""

    return {
        "sessions": [
            {
                "start": session.start.isoformat(),
                "end": session.end.isoformat(),
                "span": _format_span(session.start, session.end),
                "events": len(session.events),
                "cadence_per_hour": round(session.cadence_per_hour, 3),
                "sources": dict(session.sources),
                "latest": {
                    "message": session.events[-1].message,
                    "hash": session.events[-1].hash,
                    "timestamp": session.events[-1].timestamp,
                },
            }
            for session in sessions
        ]
    }


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Storyboard the pulse history into sessions")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to the pulse history JSON file (default: pulse_history.json)",
    )
    parser.add_argument(
        "--max-gap",
        type=float,
        default=1800.0,
        help="Maximum gap in seconds between events before starting a new session",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return JSON instead of the text storyboard",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = _parse_args(argv)

    if not args.path.exists():
        print(f"pulse history not found: {args.path}")
        return

    events = load_pulse_history(args.path)
    sessions = segment_sessions(events, max_gap_seconds=args.max_gap)

    if args.json:
        print(json.dumps(storyboard_as_dict(sessions), indent=2))
        return

    print(build_storyboard(sessions))


if __name__ == "__main__":  # pragma: no cover - CLI glue
    main()
