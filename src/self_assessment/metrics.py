"""Compliance metrics derived from telemetry events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from src.telemetry import ConsentState, TelemetryEvent


@dataclass(frozen=True)
class ComplianceMetrics:
    """Snapshot of compliance-oriented telemetry statistics."""

    total_events: int
    opted_in_events: int
    opt_out_blocked: int
    consent_unknown: int
    opt_in_ratio: float


class ComplianceEvaluator:
    """Compute compliance metrics over telemetry events."""

    def compute(self, events: Iterable[TelemetryEvent]) -> ComplianceMetrics:
        total = 0
        opted_in = 0
        blocked = 0
        unknown = 0
        for event in events:
            total += 1
            if event.consent_snapshot is ConsentState.OPTED_IN:
                opted_in += 1
            elif event.consent_snapshot is ConsentState.OPTED_OUT:
                blocked += 1
            else:
                unknown += 1
        ratio = (opted_in / total) if total else 0.0
        return ComplianceMetrics(
            total_events=total,
            opted_in_events=opted_in,
            opt_out_blocked=blocked,
            consent_unknown=unknown,
            opt_in_ratio=ratio,
        )

    def detect_anomalies(self, metrics: ComplianceMetrics) -> List[str]:
        """Return human-readable notices when thresholds are exceeded."""

        notices: List[str] = []
        if metrics.opt_in_ratio < 0.8:
            notices.append("Opt-in ratio fell below 80%. Investigate consent flows.")
        if metrics.opt_out_blocked > 0:
            notices.append("Events associated with opt-out contexts were blocked as expected.")
        if metrics.consent_unknown > 0:
            notices.append(
                "Some events were recorded with unknown consent. Review onboarding prompts."
            )
        return notices


__all__ = ["ComplianceMetrics", "ComplianceEvaluator"]
