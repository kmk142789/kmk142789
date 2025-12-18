"""Pulse ledger forecasting utilities.

The forecasting helpers combine the cadence analytics from
:mod:`echo.pulse_health` with projections that look ahead across a configurable
horizon.  They are intentionally lightweight so they can run inside CI systems
and air-gapped agents without any optional dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable, List, Sequence

from echo.echo_codox_kernel import PulseEvent
from echo.pulse_health import PulseLedgerMetrics, compute_pulse_metrics

__all__ = [
    "PulseForecast",
    "load_pulse_events",
    "forecast_pulse_activity",
]


@dataclass(frozen=True)
class PulseForecast:
    """Forward-looking projection of pulse cadence and risk."""

    metrics: PulseLedgerMetrics
    horizon_hours: float
    projected_events: int
    risk_level: str
    recommendations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def expected_next_iso(self) -> str | None:
        if self.metrics.expected_next_timestamp is None:
            return None
        return _format_timestamp(self.metrics.expected_next_timestamp)

    @property
    def time_until_next_seconds(self) -> float | None:
        if self.metrics.expected_next_timestamp is None:
            return None
        now = datetime.now(tz=timezone.utc).timestamp()
        return max(0.0, self.metrics.expected_next_timestamp - now)

    def to_dict(self) -> dict[str, object]:
        return {
            "metrics": self.metrics.to_dict(),
            "horizon_hours": self.horizon_hours,
            "projected_events": self.projected_events,
            "risk_level": self.risk_level,
            "expected_next_iso": self.expected_next_iso,
            "time_until_next_seconds": self.time_until_next_seconds,
            "recommendations": list(self.recommendations),
        }

    def to_report(self) -> str:
        lines = [
            "Pulse Forecast",
            f"Status :: {self.risk_level}",
            f"Cadence :: {self.metrics.cadence_rating}",
            f"Events projected (next {self.horizon_hours:.1f}h) :: {self.projected_events}",
        ]

        next_iso = self.expected_next_iso or "n/a"
        lines.append(f"Next expected pulse :: {next_iso}")

        if self.recommendations:
            lines.append("")
            lines.append("Recommended actions:")
            for action in self.recommendations:
                lines.append(f"- {action}")
        return "\n".join(lines)


def load_pulse_events(path: Path) -> List[PulseEvent]:
    """Parse pulse events from a JSON ledger file.

    Invalid entries are ignored so callers can run against partially written or
    manually edited histories without failing entirely.
    """

    if not path.exists():
        return []

    try:
        raw_entries: Sequence[dict] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    events: List[PulseEvent] = []
    for entry in raw_entries:
        try:
            timestamp = float(entry.get("timestamp"))
            message = str(entry.get("message", ""))
        except (TypeError, ValueError):
            continue
        event = PulseEvent(timestamp=timestamp, message=message)
        if "hash" in entry:
            event.hash = str(entry["hash"])
        events.append(event)

    events.sort(key=lambda event: event.timestamp)
    return events


def forecast_pulse_activity(
    events: Iterable[PulseEvent],
    *,
    now: float | None = None,
    horizon_hours: float = 168.0,
    warning_hours: float = 24.0,
    critical_hours: float = 72.0,
) -> PulseForecast:
    """Project the pulse cadence and suggest remediation actions.

    The forecast stitches together historical cadence metrics with a simple
    projection to flag risks across the upcoming horizon.  It intentionally
    limits itself to deterministic, dependency-free logic so it can execute in
    continuous integration pipelines.
    """

    horizon_hours = max(horizon_hours, 0.0)
    metrics = compute_pulse_metrics(
        events,
        now=now,
        warning_hours=warning_hours,
        critical_hours=critical_hours,
    )

    projected_events = _project_events(metrics, horizon_hours)
    risk_level = _derive_risk_level(metrics)
    recommendations = _build_recommendations(metrics, risk_level, horizon_hours)

    return PulseForecast(
        metrics=metrics,
        horizon_hours=horizon_hours,
        projected_events=projected_events,
        risk_level=risk_level,
        recommendations=tuple(recommendations),
    )


def _project_events(metrics: PulseLedgerMetrics, horizon_hours: float) -> int:
    if metrics.median_interval_seconds is None or metrics.median_interval_seconds <= 0:
        return 0
    horizon_seconds = horizon_hours * 3600.0
    return int(horizon_seconds // metrics.median_interval_seconds)


def _derive_risk_level(metrics: PulseLedgerMetrics) -> str:
    if metrics.total_events == 0:
        return "empty"

    status = metrics.status
    if status == "critical":
        return "critical"
    if status == "warning":
        return "warning"

    if metrics.cadence_rating == "steady":
        return "steady"
    if metrics.cadence_rating == "variable":
        return "watch"
    return "warning"


def _build_recommendations(
    metrics: PulseLedgerMetrics, risk_level: str, horizon_hours: float
) -> List[str]:
    actions: List[str] = []

    if metrics.total_events == 0:
        actions.append("Seed the first pulse to establish cadence.")
        return actions

    if risk_level in {"critical", "warning"}:
        actions.append(
            "Emit a fresh pulse with remediation notes to reset cadence risk levels."
        )

    if metrics.cadence_rating == "erratic":
        actions.append(
            "Stabilise pulse timing; consider pairing pulses with code review checkpoints."
        )
    elif metrics.cadence_rating == "variable":
        actions.append("Standardise pulse intervals to lift cadence from variable to steady.")

    if metrics.median_interval_seconds and metrics.median_interval_seconds > 0:
        forecasted_days = horizon_hours / 24.0
        actions.append(
            f"Within the next {forecasted_days:.1f} days, aim for at least {max(1, _project_events(metrics, horizon_hours))}"
            " scheduled pulses."
        )

    return actions


def _format_timestamp(timestamp: float) -> str:
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
