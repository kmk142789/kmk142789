"""Utility for summarizing the repository's pulse history logs.

This module provides a small command line helper that reads a pulse history
JSON file (``pulse_history.json`` by default) and prints summary information
such as the first and last recorded pulses, the average interval between
entries, and a frequency table of message prefixes. The functions are
implemented in a reusable way so that they can be imported by tests or other
scripts without relying on CLI parsing.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence


@dataclass(frozen=True)
class PulseSummary:
    """Summary statistics for a pulse history dataset."""

    count: int
    first_timestamp: str
    last_timestamp: str
    first_message: str
    last_message: str
    average_interval_seconds: float | None
    prefix_counts: Mapping[str, int]


def _format_timestamp(timestamp: float) -> str:
    """Convert a Unix timestamp to an ISO-8601 string in UTC."""

    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _extract_message_prefix(message: str) -> str:
    """Return a short prefix for a pulse message.

    The pulse history uses ``<emoji> action:details`` as its convention. When
    a colon is present, the portion before the first colon is used as the
    prefix, otherwise the entire message is treated as the prefix.
    """

    cleaned = message.strip()
    if not cleaned:
        return ""
    if ":" in cleaned:
        return cleaned.split(":", 1)[0]
    return cleaned


def summarize_pulse_history(entries: Sequence[Mapping[str, object]]) -> PulseSummary:
    """Compute statistics for the provided pulse history entries.

    Parameters
    ----------
    entries:
        A sequence of pulse dictionaries containing at least ``timestamp`` and
        ``message`` keys.

    Returns
    -------
    PulseSummary
        A dataclass with aggregate information about the history.

    Raises
    ------
    ValueError
        If the sequence is empty or required keys are missing.
    """

    if not entries:
        raise ValueError("pulse history is empty")

    try:
        sorted_entries = sorted(entries, key=lambda e: float(e["timestamp"]))
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise ValueError("pulse entries must include 'timestamp'") from exc

    first = sorted_entries[0]
    last = sorted_entries[-1]

    try:
        first_ts = float(first["timestamp"])
        last_ts = float(last["timestamp"])
    except (TypeError, ValueError, KeyError) as exc:  # pragma: no cover
        raise ValueError("pulse timestamps must be numeric") from exc

    prefix_counts = Counter(
        _extract_message_prefix(str(entry.get("message", ""))) for entry in entries
    )
    sorted_prefix_counts = dict(
        sorted(prefix_counts.items(), key=lambda item: (-item[1], item[0]))
    )

    average_interval = None
    if len(sorted_entries) > 1:
        average_interval = (last_ts - first_ts) / (len(sorted_entries) - 1)

    return PulseSummary(
        count=len(sorted_entries),
        first_timestamp=_format_timestamp(first_ts),
        last_timestamp=_format_timestamp(last_ts),
        first_message=str(first.get("message", "")),
        last_message=str(last.get("message", "")),
        average_interval_seconds=average_interval,
        prefix_counts=sorted_prefix_counts,
    )


def load_pulse_history(path: Path) -> List[MutableMapping[str, object]]:
    """Load pulse history entries from ``path``.

    The function raises ``FileNotFoundError`` if the path does not exist and
    ``json.JSONDecodeError`` if the file does not contain valid JSON.
    """

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("pulse history must be a JSON array")

    entries: List[MutableMapping[str, object]] = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, MutableMapping):
            raise ValueError(f"pulse entry at index {idx} must be an object")
        entries.append(entry)
    return entries


def _format_prefix_table(prefix_counts: Mapping[str, int], *, limit: int | None = None) -> str:
    """Return a formatted string table for prefix counts."""

    items = list(prefix_counts.items())
    if isinstance(limit, int):
        items = items[:max(limit, 0)]
    rows: Iterable[str] = (f"- {prefix or '[empty]'} :: {count}" for prefix, count in items)
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``pulse_history_summary`` CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to the pulse history JSON file (default: pulse_history.json)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of message prefixes to display (default: 5)",
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=0,
        help="Show the last N pulses after the summary (default: 0)",
    )
    args = parser.parse_args(argv)

    entries = load_pulse_history(args.history)
    summary = summarize_pulse_history(entries)

    print(f"Total pulses: {summary.count}")
    print(f"First pulse: {summary.first_timestamp} :: {summary.first_message}")
    print(f"Last pulse:  {summary.last_timestamp} :: {summary.last_message}")
    if summary.average_interval_seconds is not None:
        print(f"Average interval: {summary.average_interval_seconds:.2f} seconds")
    else:
        print("Average interval: n/a")

    print("\nTop message prefixes:")
    table = _format_prefix_table(summary.prefix_counts, limit=args.top)
    if table:
        print(table)
    else:
        print("(no prefixes)")

    if args.recent:
        print(f"\nMost recent {args.recent} pulses:")
        for entry in entries[-args.recent :]:
            ts = _format_timestamp(float(entry["timestamp"]))
            print(f"- {ts} :: {entry.get('message', '')}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
