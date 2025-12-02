"""Pulse ledger analytics helpers used by ``echoctl pulse``.

The helper functions compute high-level cadence metrics from the raw pulse
history so command-line and programmatic callers can render consistent status
summaries.  The calculations are intentionally lightweight – no external
dependencies – so they can run inside constrained automation environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, median, pstdev
from typing import Iterable, List, Optional

from .echo_codox_kernel import PulseEvent


@dataclass(frozen=True)
class PulseLedgerMetrics:
    """Aggregate statistics derived from the pulse ledger."""

    total_events: int
    first_timestamp: Optional[float]
    last_timestamp: Optional[float]
    span_seconds: Optional[float]
    average_interval_seconds: Optional[float]
    median_interval_seconds: Optional[float]
    daily_rate: Optional[float]
    time_since_last_seconds: Optional[float]
    status: str
    warning_threshold_seconds: float
    critical_threshold_seconds: float
    cadence_score: Optional[float]
    cadence_rating: str
    expected_next_timestamp: Optional[float]
    overdue_seconds: Optional[float]

    @property
    def first_timestamp_iso(self) -> Optional[str]:
        return _format_timestamp(self.first_timestamp)

    @property
    def last_timestamp_iso(self) -> Optional[str]:
        return _format_timestamp(self.last_timestamp)

    @property
    def expected_next_timestamp_iso(self) -> Optional[str]:
        return _format_timestamp(self.expected_next_timestamp)

    def to_dict(self) -> dict:
        return {
            "total_events": self.total_events,
            "first_timestamp": self.first_timestamp,
            "first_timestamp_iso": self.first_timestamp_iso,
            "last_timestamp": self.last_timestamp,
            "last_timestamp_iso": self.last_timestamp_iso,
            "span_seconds": self.span_seconds,
            "average_interval_seconds": self.average_interval_seconds,
            "median_interval_seconds": self.median_interval_seconds,
            "daily_rate": self.daily_rate,
            "time_since_last_seconds": self.time_since_last_seconds,
            "status": self.status,
            "warning_threshold_seconds": self.warning_threshold_seconds,
            "critical_threshold_seconds": self.critical_threshold_seconds,
            "cadence_score": self.cadence_score,
            "cadence_rating": self.cadence_rating,
            "expected_next_timestamp": self.expected_next_timestamp,
            "expected_next_timestamp_iso": self.expected_next_timestamp_iso,
            "overdue_seconds": self.overdue_seconds,
        }


def compute_pulse_metrics(
    events: Iterable[PulseEvent],
    *,
    now: Optional[float] = None,
    warning_hours: float = 24.0,
    critical_hours: float = 72.0,
) -> PulseLedgerMetrics:
    """Return cadence metrics describing ``events``.

    Parameters
    ----------
    events:
        Pulse ledger entries sorted chronologically.
    now:
        Optional timestamp (seconds since epoch).  Defaults to the current UTC
        time; dependency injection keeps tests deterministic.
    warning_hours / critical_hours:
        Thresholds used to derive the ``status`` field.  When the time since the
        last event is greater than or equal to ``warning_hours`` the ledger is
        flagged as ``warning``.  Crossing ``critical_hours`` results in the
        ``critical`` status.

    The returned :class:`PulseLedgerMetrics` also includes derived cadence
    scores. ``cadence_score`` captures the variability of the pulse intervals on
    a 0–100 scale, while ``cadence_rating`` provides a coarse label
    (``steady``, ``variable``, or ``erratic``). When there are too few events to
    infer cadence these fields fall back to ``None`` and ``"unknown"``.
    """

    event_list: List[PulseEvent] = list(events)
    warning_threshold_seconds = max(warning_hours, 0.0) * 3600.0
    critical_threshold_seconds = max(critical_hours, 0.0) * 3600.0

    if not event_list:
        return PulseLedgerMetrics(
            total_events=0,
            first_timestamp=None,
            last_timestamp=None,
            span_seconds=None,
            average_interval_seconds=None,
            median_interval_seconds=None,
            daily_rate=None,
            time_since_last_seconds=None,
            status="empty",
            warning_threshold_seconds=warning_threshold_seconds,
            critical_threshold_seconds=critical_threshold_seconds,
            cadence_score=None,
            cadence_rating="unknown",
            expected_next_timestamp=None,
            overdue_seconds=None,
        )

    first_ts = event_list[0].timestamp
    last_ts = event_list[-1].timestamp
    span_seconds = max(0.0, last_ts - first_ts)

    intervals: List[float] = []
    if len(event_list) > 1:
        intervals = [
            max(0.0, event_list[index].timestamp - event_list[index - 1].timestamp)
            for index in range(1, len(event_list))
        ]

    avg_interval = mean(intervals) if intervals else None
    median_interval = median(intervals) if intervals else None
    daily_rate = None
    if span_seconds > 0:
        daily_rate = (len(event_list) / span_seconds) * 86400.0

    cadence_score = None
    cadence_rating = "unknown"
    if avg_interval and avg_interval > 0:
        variability = pstdev(intervals) if intervals else 0.0
        cadence_score = max(0.0, (1 - min(variability / avg_interval, 2.0) / 2.0) * 100)
        cadence_score = round(cadence_score, 2)
        if cadence_score >= 75:
            cadence_rating = "steady"
        elif cadence_score >= 40:
            cadence_rating = "variable"
        else:
            cadence_rating = "erratic"

    current_time = now if now is not None else datetime.now(tz=timezone.utc).timestamp()
    time_since_last = max(0.0, current_time - last_ts)

    expected_next_timestamp = None
    overdue_seconds = None
    if median_interval is not None:
        expected_next_timestamp = last_ts + median_interval
        overdue_seconds = max(0.0, current_time - expected_next_timestamp)

    status = "fresh"
    if time_since_last >= critical_threshold_seconds > 0:
        status = "critical"
    elif time_since_last >= warning_threshold_seconds > 0:
        status = "warning"

    return PulseLedgerMetrics(
        total_events=len(event_list),
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        span_seconds=span_seconds,
        average_interval_seconds=avg_interval,
        median_interval_seconds=median_interval,
        daily_rate=daily_rate,
        time_since_last_seconds=time_since_last,
        status=status,
        warning_threshold_seconds=warning_threshold_seconds,
        critical_threshold_seconds=critical_threshold_seconds,
        cadence_score=cadence_score,
        cadence_rating=cadence_rating,
        expected_next_timestamp=expected_next_timestamp,
        overdue_seconds=overdue_seconds,
    )


def _format_timestamp(timestamp: Optional[float]) -> Optional[str]:
    if timestamp is None:
        return None
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
