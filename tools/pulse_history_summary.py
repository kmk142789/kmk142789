#!/usr/bin/env python3
"""Generate concise statistics for entries stored in ``pulse_history.json``.

Historically this module only printed a textual summary.  The refactor keeps the
command line interface but also exposes reusable helpers that tests and API
routes can import directly.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence


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


@dataclass(frozen=True)
class PulseHistorySummary:
    """Aggregate statistics extracted from raw pulse history entries."""

    count: int
    first_timestamp: str
    last_timestamp: str
    first_message: str
    last_message: str
    average_interval_seconds: float
    prefix_counts: Mapping[str, int]


def _resolve_history_path(path: Path) -> Path:
    """Return a path to ``pulse_history.json`` allowing repository-relative lookups."""

    if path.exists():
        return path

    repo_root = Path(__file__).resolve().parent.parent
    candidate = repo_root / path
    if candidate.exists():
        return candidate

    raise FileNotFoundError(f"File not found: {path}")


def load_events(path: Path | str) -> List[PulseEvent]:
    """Load the JSON log into a list of :class:`PulseEvent` objects."""

    raw_entries = json.loads(_resolve_history_path(Path(path)).read_text())
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


def load_pulse_history(path: Path | str) -> List[MutableMapping[str, object]]:
    """Return normalised pulse history entries sorted by timestamp.

    The helper keeps the implementation intentionally lightweight so it can be
    used by command line utilities and FastAPI services alike.  Each entry is a
    mutable mapping containing at least the ``timestamp`` and ``message`` keys.
    Unknown keys are preserved to avoid throwing away metadata that other tools
    may rely on.
    """

    resolved = _resolve_history_path(Path(path))
    raw_entries = json.loads(resolved.read_text())
    if not isinstance(raw_entries, list):
        raise ValueError("pulse history file must contain a JSON array of entries")

    entries: List[MutableMapping[str, object]] = []
    for index, entry in enumerate(raw_entries):
        if not isinstance(entry, Mapping):
            raise ValueError(f"pulse history entry {index} must be a JSON object")
        try:
            timestamp = float(entry["timestamp"])
        except KeyError as exc:
            raise ValueError(f"pulse history entry {index} missing 'timestamp'") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"pulse history entry {index} timestamp must be numeric"
            ) from exc

        normalised: MutableMapping[str, object] = dict(entry)
        normalised["timestamp"] = timestamp
        if "message" in normalised:
            normalised["message"] = str(normalised["message"])
        else:
            raise ValueError(f"pulse history entry {index} missing 'message'")

        entries.append(normalised)

    entries.sort(key=lambda item: item["timestamp"])
    return entries


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


def _format_prefix_table(prefix_counts: Mapping[str, int], *, limit: int | None = None) -> str:
    """Render ``prefix_counts`` into a stable, human-friendly bullet list."""

    filtered = [(prefix, count) for prefix, count in prefix_counts.items() if prefix]
    filtered.sort(key=lambda item: (-item[1], item[0]))
    if limit is not None and limit >= 0:
        filtered = filtered[:limit]
    return "\n".join(f"- {prefix} :: {count}" for prefix, count in filtered)


def _prefix_counts(entries: Sequence[Mapping[str, object]]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        message = str(entry.get("message", ""))
        prefix = message.split(":", maxsplit=1)[0].strip()
        if prefix:
            counts[prefix] = counts.get(prefix, 0) + 1
    return counts


def summarize_pulse_history(entries: Sequence[Mapping[str, object]]) -> PulseHistorySummary:
    """Return high level statistics for ``entries``.

    Parameters
    ----------
    entries:
        Sequence of mappings containing at least the ``timestamp`` and
        ``message`` keys.  The function accepts the direct JSON dictionaries
        produced by :func:`load_pulse_history` as well as minimal synthetic test
        data.
    """

    if not entries:
        raise ValueError("pulse history is empty")

    normalised: List[tuple[float, str]] = []
    for index, entry in enumerate(entries):
        try:
            timestamp = float(entry["timestamp"])
        except KeyError as exc:
            raise ValueError(f"entry {index} missing 'timestamp'") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"entry {index} timestamp must be numeric") from exc

        message_obj = entry.get("message")
        if message_obj is None:
            raise ValueError(f"entry {index} missing 'message'")
        message = str(message_obj)
        normalised.append((timestamp, message))

    normalised.sort(key=lambda item: item[0])
    first_ts, first_message = normalised[0]
    last_ts, last_message = normalised[-1]

    intervals = [
        current[0] - previous[0]
        for previous, current in zip(normalised, normalised[1:])
    ]
    average_interval = sum(intervals) / len(intervals) if intervals else 0.0

    summary = PulseHistorySummary(
        count=len(normalised),
        first_timestamp=datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat(),
        last_timestamp=datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat(),
        first_message=first_message,
        last_message=last_message,
        average_interval_seconds=average_interval,
        prefix_counts=dict(sorted(_prefix_counts(entries).items(), key=lambda item: (-item[1], item[0]))),
    )
    return summary


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
    path = _resolve_history_path(args.path)

    entries = load_pulse_history(path)
    summary = summarize_pulse_history(entries)

    lines = [
        f"Total events: {summary.count}",
        f"First event: {summary.first_timestamp} — {summary.first_message}",
        f"Last event:  {summary.last_timestamp} — {summary.last_message}",
    ]
    lines.append(
        "Average interval: {:.2f} seconds".format(summary.average_interval_seconds)
    )

    prefix_table = _format_prefix_table(summary.prefix_counts)
    if prefix_table:
        lines.append("")
        lines.append("Top prefixes:")
        lines.append(prefix_table)

    print("\n".join(lines))


if __name__ == "__main__":
    main()
