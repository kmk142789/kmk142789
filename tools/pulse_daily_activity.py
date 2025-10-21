"""Utilities for visualizing daily activity from the pulse history."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .pulse_history_summary import load_pulse_history


@dataclass(frozen=True)
class DailyActivity:
    """A single day's pulse activity."""

    date: str
    count: int


@dataclass(frozen=True)
class DailyActivitySummary:
    """Aggregate statistics describing daily pulse activity."""

    total_days: int
    total_entries: int
    busiest_day: DailyActivity | None
    quietest_day: DailyActivity | None
    activity: Sequence[DailyActivity]


def _ensure_numeric_timestamp(entry: Mapping[str, object]) -> float:
    """Return the numeric timestamp for ``entry`` or raise ``ValueError``."""

    try:
        return float(entry["timestamp"])
    except KeyError as exc:
        raise ValueError("pulse entry must include 'timestamp'") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("pulse entry timestamp must be numeric") from exc


def calculate_daily_activity(
    entries: Sequence[Mapping[str, object]], *, tz: timezone = timezone.utc
) -> DailyActivitySummary:
    """Return activity counts grouped by day.

    Parameters
    ----------
    entries:
        Pulse history entries containing ``timestamp`` values.
    tz:
        Timezone to use for date conversion. Defaults to UTC.
    """

    day_counts: dict[str, int] = {}
    for entry in entries:
        timestamp = _ensure_numeric_timestamp(entry)
        day = datetime.fromtimestamp(timestamp, tz=tz).date().isoformat()
        day_counts[day] = day_counts.get(day, 0) + 1

    ordered_activity = [DailyActivity(date=day, count=day_counts[day]) for day in sorted(day_counts)]

    busiest = max(ordered_activity, key=lambda item: item.count) if ordered_activity else None
    quietest = min(ordered_activity, key=lambda item: item.count) if ordered_activity else None

    return DailyActivitySummary(
        total_days=len(ordered_activity),
        total_entries=len(entries),
        busiest_day=busiest,
        quietest_day=quietest,
        activity=tuple(ordered_activity),
    )


def render_activity_table(
    activity: Iterable[DailyActivity], *, width: int = 20, bar_char: str = "█"
) -> str:
    """Render a simple text table visualizing ``activity``."""

    entries = list(activity)
    if not entries:
        return "(no activity)"

    max_count = max(item.count for item in entries)
    if max_count <= 0:
        return "\n".join(f"{item.date} | 0" for item in entries)

    width = max(width, 1)
    lines = []
    for item in entries:
        scale = item.count / max_count if max_count else 0
        bar_length = max(1, int(round(scale * width))) if item.count else 0
        bar = bar_char * bar_length if bar_length > 0 else ""
        lines.append(f"{item.date} | {item.count:3d} {bar}")
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to the pulse history JSON file (default: pulse_history.json)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=30,
        help="Maximum width of the activity bar chart (default: 30)",
    )
    parser.add_argument(
        "--bar-char",
        type=str,
        default="█",
        help="Character used to render the activity bars (default: █)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the daily activity tool."""

    args = _parse_args(argv)
    entries = load_pulse_history(args.history)
    summary = calculate_daily_activity(entries)

    print(f"Total entries: {summary.total_entries}")
    print(f"Total active days: {summary.total_days}")
    if summary.busiest_day:
        print(
            f"Busiest day: {summary.busiest_day.date} ({summary.busiest_day.count} pulses)"
        )
    if summary.quietest_day:
        print(
            f"Quietest day: {summary.quietest_day.date} ({summary.quietest_day.count} pulses)"
        )
    print()
    print(render_activity_table(summary.activity, width=args.width, bar_char=args.bar_char))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
