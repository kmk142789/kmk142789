#!/usr/bin/env python3
"""Detect anomalous behaviour inside ``pulse_history.json``.

The pulse history log keeps track of automation runs and manual updates across
ECHO tooling.  Operations teams requested a lightweight guardrail that can be
run ad-hoc to highlight suspicious gaps in activity or accidental duplicate
entries.  This module exposes reusable helpers and a small command line
interface so that other services (FastAPI endpoints, cron jobs, etc.) can reuse
its anomaly detection logic.
"""

from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

try:  # pragma: no cover - executed when running as ``python tools/...``
    from .pulse_history_summary import PulseEvent, load_events
except ImportError:  # pragma: no cover - fallback when executed as a script
    from pulse_history_summary import PulseEvent, load_events  # type: ignore


@dataclass(frozen=True)
class IntervalStatistics:
    """Descriptive statistics for inter-event intervals."""

    mean: float
    median: float
    stdev: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class IntervalAnomaly:
    """Representation of an unusually long or irregular interval."""

    start: PulseEvent
    end: PulseEvent
    interval_seconds: float
    z_score: float


@dataclass(frozen=True)
class DuplicateEventGroup:
    """Events that share an identical hash within the pulse history."""

    hash: str
    events: Tuple[PulseEvent, ...]

    @property
    def count(self) -> int:
        return len(self.events)


def _sorted_events(events: Sequence[PulseEvent]) -> List[PulseEvent]:
    return sorted(events, key=lambda event: event.timestamp)


def compute_interval_statistics(events: Sequence[PulseEvent]) -> IntervalStatistics | None:
    """Return aggregate statistics for gaps between pulse events."""

    if len(events) < 2:
        return None

    ordered = _sorted_events(events)
    intervals = [
        current.timestamp - previous.timestamp
        for previous, current in zip(ordered, ordered[1:])
    ]

    if not intervals:
        return None

    mean = statistics.fmean(intervals)
    median = statistics.median(intervals)
    stdev = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
    minimum = min(intervals)
    maximum = max(intervals)

    return IntervalStatistics(
        mean=mean,
        median=median,
        stdev=stdev,
        minimum=minimum,
        maximum=maximum,
    )


def find_interval_anomalies(
    events: Sequence[PulseEvent],
    *,
    z_threshold: float = 2.5,
    minimum_gap: float | None = 4 * 3600,
) -> List[IntervalAnomaly]:
    """Identify unusually long gaps between events.

    Parameters
    ----------
    events:
        Pulse history entries already loaded into :class:`PulseEvent` objects.
    z_threshold:
        Minimum absolute z-score required to report an interval anomaly.
    minimum_gap:
        Absolute threshold (in seconds).  Any interval equal to or larger than
        this value is flagged regardless of the z-score.  Set to ``None`` to
        disable.
    """

    if len(events) < 2:
        return []

    ordered = _sorted_events(events)
    intervals = [
        (previous, current, current.timestamp - previous.timestamp)
        for previous, current in zip(ordered, ordered[1:])
    ]

    if not intervals:
        return []

    stats = compute_interval_statistics(events)
    stdev = stats.stdev if stats is not None else 0.0
    mean = stats.mean if stats is not None else 0.0

    anomalies: List[IntervalAnomaly] = []
    for start, end, interval in intervals:
        if interval < 0:
            # Guard against malformed timestamps - treat as anomaly with high score
            anomalies.append(
                IntervalAnomaly(start=start, end=end, interval_seconds=interval, z_score=float("inf"))
            )
            continue

        z_score = 0.0
        if stdev > 0:
            z_score = (interval - mean) / stdev

        exceeds_threshold = stdev > 0 and z_score >= z_threshold
        exceeds_min_gap = minimum_gap is not None and interval >= minimum_gap

        if exceeds_threshold or exceeds_min_gap:
            anomalies.append(
                IntervalAnomaly(
                    start=start,
                    end=end,
                    interval_seconds=interval,
                    z_score=z_score,
                )
            )

    anomalies.sort(key=lambda item: item.interval_seconds, reverse=True)
    return anomalies


def find_duplicate_hash_groups(events: Sequence[PulseEvent]) -> List[DuplicateEventGroup]:
    """Return groups of events that share identical hashes."""

    buckets: dict[str, List[PulseEvent]] = {}
    for event in events:
        buckets.setdefault(event.hash, []).append(event)

    groups = [
        DuplicateEventGroup(hash=hash_value, events=tuple(_sorted_events(group)))
        for hash_value, group in buckets.items()
        if len(group) > 1
    ]

    groups.sort(key=lambda group: (-group.count, group.events[0].timestamp))
    return groups


def _format_event(event: PulseEvent) -> str:
    timestamp = event.datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{timestamp} — {event.message}"


def build_report(
    events: Sequence[PulseEvent],
    *,
    anomalies: Sequence[IntervalAnomaly],
    duplicates: Sequence[DuplicateEventGroup],
    stats: IntervalStatistics | None,
    max_duplicate_groups: int | None = 5,
) -> str:
    """Render a human-readable anomaly report."""

    if not events:
        return "No events available."

    lines: List[str] = []
    first, last = min(events, key=lambda e: e.timestamp), max(events, key=lambda e: e.timestamp)
    lines.append(f"Events analysed: {len(events)}")
    lines.append(f"Time span: {_format_event(first)} → {_format_event(last)}")

    if stats is None:
        lines.append("Not enough data to compute interval statistics.")
    else:
        lines.append(
            "Average gap: {mean:.1f}s | Median: {median:.1f}s | Std dev: {stdev:.1f}s | Min: {minimum:.1f}s | Max: {maximum:.1f}s".format(
                mean=stats.mean,
                median=stats.median,
                stdev=stats.stdev,
                minimum=stats.minimum,
                maximum=stats.maximum,
            )
        )

    lines.append("")
    lines.append("Interval anomalies:")
    if anomalies:
        for anomaly in anomalies:
            lines.append(
                "- Gap of {interval:.1f}s (z={z_score:.2f}) between {start} and {end}".format(
                    interval=anomaly.interval_seconds,
                    z_score=anomaly.z_score,
                    start=_format_event(anomaly.start),
                    end=_format_event(anomaly.end),
                )
            )
    else:
        lines.append("- None detected")

    lines.append("")
    lines.append("Duplicate hashes:")
    if duplicates:
        limit = duplicates if max_duplicate_groups is None else duplicates[:max_duplicate_groups]
        for group in limit:
            lines.append(f"- {group.hash} :: {group.count} entries")
            for event in group.events:
                lines.append(f"    • {_format_event(event)}")
        if max_duplicate_groups is not None and len(duplicates) > max_duplicate_groups:
            lines.append(f"  … {len(duplicates) - max_duplicate_groups} additional duplicate groups omitted")
    else:
        lines.append("- None detected")

    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect anomalous behaviour in pulse_history.json entries.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to the pulse history JSON file. Defaults to pulse_history.json in the repository root.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.5,
        help="Z-score threshold for flagging interval anomalies (default: 2.5).",
    )
    parser.add_argument(
        "--minimum-gap",
        type=float,
        default=4 * 3600,
        help="Minimum interval in seconds that should always be flagged (default: 14400). Use 0 to disable.",
    )
    parser.add_argument(
        "--max-duplicates",
        type=int,
        default=5,
        help="Maximum number of duplicate hash groups to display (default: 5). Use -1 for no limit.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    events = load_events(args.path)
    stats = compute_interval_statistics(events)

    minimum_gap = args.minimum_gap if args.minimum_gap > 0 else None
    anomalies = find_interval_anomalies(
        events,
        z_threshold=args.threshold,
        minimum_gap=minimum_gap,
    )

    max_duplicates = None if args.max_duplicates < 0 else args.max_duplicates
    duplicates = find_duplicate_hash_groups(events)

    report = build_report(
        events,
        anomalies=anomalies,
        duplicates=duplicates,
        stats=stats,
        max_duplicate_groups=max_duplicates,
    )
    print(report)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
