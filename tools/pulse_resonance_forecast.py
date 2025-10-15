"""Forecast upcoming Echo pulse emissions based on historical cadence.

Echo's pulse history captures the cadence of prior transmissions in
``pulse_history.json``.  The ``pulse_resonance_forecast`` tool analyses that
history and produces a forward projection of the next few pulses.  The forecast
can be rendered as a human readable table or as structured JSON for downstream
systems.

Example
-------

Generate a three point forecast using the repository defaults::

    $ python tools/pulse_resonance_forecast.py --future-count 3

Limit the analysis to the most recent eight intervals and emit JSON::

    $ python tools/pulse_resonance_forecast.py --window 8 --format json
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from tools.pulse_continuity_audit import (
    DEFAULT_HISTORY_PATH,
    PulseEvent,
    load_pulse_history,
)


@dataclass(slots=True)
class ForecastPoint:
    """Single projected pulse in the resonance timeline."""

    index: int
    expected_time: datetime
    interval_seconds: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "expected_time": self.expected_time.isoformat(),
            "interval_seconds": self.interval_seconds,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class ResonanceForecast:
    """Complete forecast bundle and provenance."""

    anchor: Optional[str]
    history_count: int
    interval_count: int
    average_interval: Optional[float]
    stddev_interval: Optional[float]
    forecast: List[ForecastPoint]
    warnings: List[str]

    def to_dict(self) -> dict:
        return {
            "anchor": self.anchor,
            "history_count": self.history_count,
            "interval_count": self.interval_count,
            "average_interval_seconds": self.average_interval,
            "stddev_interval_seconds": self.stddev_interval,
            "forecast": [point.to_dict() for point in self.forecast],
            "warnings": list(self.warnings),
        }

    def render_text(self) -> str:
        lines = [
            "Echo Pulse Resonance Forecast",
            f"  Anchor         : {self.anchor or '∅'}",
            f"  History Points : {self.history_count}",
            f"  Interval Count : {self.interval_count}",
        ]
        if self.average_interval is not None:
            lines.append(
                f"  Mean Interval  : {self.average_interval / 3600.0:.2f} hours"
            )
        if self.stddev_interval is not None:
            lines.append(
                f"  Interval σ     : {self.stddev_interval / 3600.0:.2f} hours"
            )
        if self.forecast:
            lines.append("Forecast:")
            for point in self.forecast:
                delta_hours = point.interval_seconds / 3600.0
                lines.append(
                    "  - +{index:02d}  {ts}  Δ {delta:.2f} h  confidence {conf:.2f}".format(
                        index=point.index,
                        ts=point.expected_time.isoformat(),
                        delta=delta_hours,
                        conf=point.confidence,
                    )
                )
        else:
            lines.append("Forecast: ∅ (insufficient history)")
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {warning}" for warning in self.warnings)
        return "\n".join(lines)


def _sort_events(events: Iterable[PulseEvent]) -> List[PulseEvent]:
    return sorted(events, key=lambda event: event.timestamp)


def _event_intervals(events: Sequence[PulseEvent]) -> List[float]:
    intervals: List[float] = []
    for previous, current in zip(events, events[1:]):
        delta = current.timestamp - previous.timestamp
        if delta > 0:
            intervals.append(delta)
    return intervals


def _window_intervals(intervals: Sequence[float], window: Optional[int]) -> List[float]:
    if window is None or window <= 0 or window >= len(intervals):
        return list(intervals)
    return list(intervals[-window:])


def _confidence_score(mean_interval: Optional[float], stddev_interval: Optional[float]) -> float:
    if mean_interval is None or mean_interval <= 0:
        return 0.0
    if stddev_interval is None:
        return 1.0
    ratio = stddev_interval / mean_interval
    bounded = min(max(ratio, 0.0), 4.0)
    confidence = 1.0 / (1.0 + bounded)
    return round(confidence, 4)


def generate_forecast(
    events: Sequence[PulseEvent],
    *,
    anchor: Optional[str] = None,
    future_count: int = 3,
    window: Optional[int] = None,
    now: Optional[datetime] = None,
) -> ResonanceForecast:
    warnings: List[str] = []
    ordered = _sort_events(events)
    if not ordered:
        warnings.append("pulse history is empty")
        return ResonanceForecast(
            anchor=anchor,
            history_count=0,
            interval_count=0,
            average_interval=None,
            stddev_interval=None,
            forecast=[],
            warnings=warnings,
        )

    intervals = _event_intervals(ordered)
    if not intervals:
        warnings.append("pulse history contains a single event; need at least two")
        return ResonanceForecast(
            anchor=anchor,
            history_count=len(ordered),
            interval_count=0,
            average_interval=None,
            stddev_interval=None,
            forecast=[],
            warnings=warnings,
        )

    recent_intervals = _window_intervals(intervals, window)
    if not recent_intervals:
        warnings.append("window eliminated all usable intervals; reverting to full history")
        recent_intervals = intervals

    mean_interval = sum(recent_intervals) / len(recent_intervals)
    stddev_interval: Optional[float]
    if len(recent_intervals) > 1:
        variance = sum((value - mean_interval) ** 2 for value in recent_intervals) / (
            len(recent_intervals) - 1
        )
        stddev_interval = math.sqrt(variance)
    else:
        stddev_interval = None

    base_confidence = _confidence_score(mean_interval, stddev_interval)

    last_timestamp = ordered[-1].moment
    origin_time = now.astimezone(timezone.utc) if now else last_timestamp
    if now and now.tzinfo is None:
        origin_time = now.replace(tzinfo=timezone.utc)

    # Start forecasting from whichever is later: the final recorded event or the supplied "now".
    if origin_time < last_timestamp:
        origin_time = last_timestamp

    forecast_points: List[ForecastPoint] = []
    if mean_interval <= 0:
        warnings.append("mean interval collapsed to zero; cannot project forward")
    else:
        cursor = origin_time
        for step in range(1, max(future_count, 0) + 1):
            cursor += timedelta(seconds=mean_interval)
            confidence = round(min(1.0, base_confidence ** step), 4)
            forecast_points.append(
                ForecastPoint(
                    index=step,
                    expected_time=cursor,
                    interval_seconds=mean_interval,
                    confidence=confidence,
                )
            )

    return ResonanceForecast(
        anchor=anchor,
        history_count=len(ordered),
        interval_count=len(recent_intervals),
        average_interval=mean_interval,
        stddev_interval=stddev_interval,
        forecast=forecast_points,
        warnings=warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Forecast upcoming Echo pulses using historical resonance data.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Path to pulse_history.json (default: repository root pulse_history.json)",
    )
    parser.add_argument(
        "--future-count",
        type=int,
        default=3,
        help="Number of future pulse projections to generate (default: 3)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=None,
        help="Optional number of most recent intervals to use for averaging",
    )
    parser.add_argument(
        "--anchor",
        type=str,
        default=None,
        help="Label to include in the forecast output",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        events = load_pulse_history(args.history)
    except Exception as exc:  # pragma: no cover - argparse already reports errors
        parser.error(str(exc))

    forecast = generate_forecast(
        events,
        anchor=args.anchor,
        future_count=args.future_count,
        window=args.window,
    )

    if args.format == "json":
        print(json.dumps(forecast.to_dict(), indent=2))
    else:
        print(forecast.render_text())

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
