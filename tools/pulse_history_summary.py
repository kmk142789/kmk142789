#!/usr/bin/env python3
"""Generate a quick summary of the repository's pulse history log.

The script reads ``pulse_history.json`` and prints a handful of statistics that
make it easier to reason about the activity recorded in the ledger.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping


@dataclass(frozen=True)
class PulseEvent:
    """Single event entry loaded from ``pulse_history.json``."""

    timestamp: float
    message: str
    hash: str

    @property
    def datetime(self) -> datetime:
        """Return the timestamp as a timezone-aware ``datetime`` object."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)

    @property
    def category(self) -> str:
        """Return the high-level category encoded in the ``message`` field."""

        return self.message.split(":", maxsplit=1)[0]


def load_events(path: Path) -> List[PulseEvent]:
    """Load the JSON log into a list of :class:`PulseEvent` objects."""

    raw_entries = json.loads(path.read_text())
    events: List[PulseEvent] = []
    for index, entry in enumerate(raw_entries):
        try:
            events.append(
                PulseEvent(
                    timestamp=float(entry["timestamp"]),
                    message=str(entry["message"]),
                    hash=str(entry["hash"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Malformed entry at index {index}: {entry!r}") from exc
    return events


def count_by_category(events: Iterable[PulseEvent]) -> Mapping[str, int]:
    """Return the total number of events for each category."""

    counts: dict[str, int] = {}
    for event in events:
        counts[event.category] = counts.get(event.category, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def format_datetime(value: datetime) -> str:
    """Convert a ``datetime`` into a short, human-readable string."""

    return value.strftime("%Y-%m-%d %H:%M:%S %Z")


def summarize(events: List[PulseEvent]) -> str:
    """Produce a human-readable summary report for the provided events."""

    if not events:
        return "No events found."

    sorted_events = sorted(events, key=lambda event: event.timestamp)
    first, last = sorted_events[0], sorted_events[-1]
    counts = count_by_category(events)

    lines = [
        f"Total events: {len(events)}",
        f"Time span: {format_datetime(first.datetime)} → {format_datetime(last.datetime)}",
        "",
        "Events by category:",
    ]

    width = max(len(category) for category in counts)
    for category, amount in counts.items():
        lines.append(f"  {category.ljust(width)} : {amount}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise entries from pulse_history.json.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to the pulse history JSON file. Defaults to pulse_history.json in the repository root.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path: Path = args.path
    if not path.exists():
        repo_root = Path(__file__).resolve().parent.parent
        candidate = repo_root / path
        if candidate.exists():
            path = candidate
        else:
            raise SystemExit(f"File not found: {path}")

    events = load_events(path)
    report = summarize(events)
    print(report)


if __name__ == "__main__":
    main()
