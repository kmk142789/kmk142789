"""Reporting utilities for compliance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from src.telemetry.storage import TelemetryStorage

from .metrics import ComplianceEvaluator, ComplianceMetrics


@dataclass
class ComplianceReport:
    """A structured compliance report for downstream tooling."""

    generated_at: datetime
    metrics: ComplianceMetrics
    notices: list[str]
    audit_entries: list[Mapping[str, object]]


class ReportEmitter:
    """Coordinate compliance evaluations and emit reports."""

    def __init__(
        self,
        *,
        storage: TelemetryStorage,
        evaluator: ComplianceEvaluator | None = None,
    ) -> None:
        self.storage = storage
        self.evaluator = evaluator or ComplianceEvaluator()

    def generate(self, audit_entries: Iterable[Mapping[str, object]]) -> ComplianceReport:
        events = list(self.storage.read())
        metrics = self.evaluator.compute(events)
        notices = self.evaluator.detect_anomalies(metrics)
        return ComplianceReport(
            generated_at=datetime.now(timezone.utc),
            metrics=metrics,
            notices=notices,
            audit_entries=list(audit_entries),
        )

    def export_json(self, report: ComplianceReport, path: Path) -> None:
        payload = {
            "generated_at": report.generated_at.astimezone(timezone.utc).isoformat(),
            "metrics": {
                "total_events": report.metrics.total_events,
                "opted_in_events": report.metrics.opted_in_events,
                "opt_out_blocked": report.metrics.opt_out_blocked,
                "consent_unknown": report.metrics.consent_unknown,
                "opt_in_ratio": report.metrics.opt_in_ratio,
            },
            "notices": report.notices,
            "audit_entries": list(report.audit_entries),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_dumps(payload), encoding="utf-8")


def json_dumps(payload: Mapping[str, object]) -> str:
    import json

    return json.dumps(payload, indent=2, default=str)


__all__ = ["ComplianceReport", "ReportEmitter"]
