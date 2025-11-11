"""Bridge the compliance engine into Atlas workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterable, Mapping, Sequence

from atlas.metrics import AtlasMetricsService

try:  # Optional dependency for runtime usage
    from echo_atlas.service import AtlasService
except Exception:  # pragma: no cover - atlas is optional for unit tests
    AtlasService = None  # type: ignore[assignment]

from src.self_assessment import ReportEmitter
from src.self_assessment.reporting import ComplianceReport
from src.telemetry.schema import TelemetryEvent
from src.telemetry.storage import JsonlTelemetryStorage, TelemetryStorage


DEFAULT_TELEMETRY_PATH = Path("state/telemetry/events.jsonl")
DEFAULT_REPORT_PATH = Path("reports/compliance/atlas_compliance_report.json")
DEFAULT_METRICS_PATH = Path("reports/compliance/atlas_metrics.json")


@dataclass(slots=True)
class AtlasJobResult:
    """Outcome from executing the compliance Atlas job."""

    duration_seconds: float
    counters: Mapping[str, int]
    notices: Sequence[str]
    highlight: str
    report_path: Path


def _build_audit_entries(events: Iterable[TelemetryEvent]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for event in events:
        context = event.context
        pseudo_id = context.pseudonymous_id
        if pseudo_id in seen:
            continue
        seen.add(pseudo_id)
        consent_recorded = (
            context.consent_recorded_at.isoformat()
            if context.consent_recorded_at
            else None
        )
        entries.append(
            {
                "pseudonymous_id": pseudo_id,
                "consent_state": context.consent_state.value,
                "consent_recorded_at": consent_recorded,
                "session_label": context.session_label,
            }
        )
    return entries


class ComplianceAtlasJob:
    """Expose the compliance engine as an Atlas-compatible job."""

    def __init__(
        self,
        *,
        telemetry_path: Path = DEFAULT_TELEMETRY_PATH,
        audit_path: Path | None = None,
        output_path: Path = DEFAULT_REPORT_PATH,
        metrics_service: AtlasMetricsService | None = None,
        atlas_service: AtlasService | None = None,
    ) -> None:
        self.telemetry_path = telemetry_path
        self.audit_path = audit_path
        self.output_path = output_path
        self.metrics = metrics_service or AtlasMetricsService()
        self.atlas_service = atlas_service
        self._storage: TelemetryStorage | None = None
        self._emitter: ReportEmitter | None = None

    @property
    def storage(self) -> TelemetryStorage:
        if self._storage is None:
            self._storage = JsonlTelemetryStorage(self.telemetry_path)
        return self._storage

    @property
    def emitter(self) -> ReportEmitter:
        if self._emitter is None:
            self._emitter = ReportEmitter(storage=self.storage)
        return self._emitter

    def _load_audit_entries(self, events: Sequence[TelemetryEvent]) -> Sequence[Mapping[str, object]]:
        if self.audit_path and self.audit_path.exists():
            payload = json.loads(self.audit_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [entry for entry in payload if isinstance(entry, Mapping)]
        return _build_audit_entries(events)

    def _highlight_for(self, report: ComplianceReport) -> str:
        metrics = report.metrics
        notice_count = len(report.notices)
        ratio = metrics.opt_in_ratio * 100
        return (
            "Compliance Engine processed "
            f"{metrics.total_events} events ({metrics.opted_in_events} opted-in, "
            f"{metrics.opt_out_blocked} blocked, {metrics.consent_unknown} unknown). "
            f"Opt-in ratio {ratio:.1f}% | Notices {notice_count}."
        )

    def execute(self) -> AtlasJobResult:
        start = perf_counter()
        events = list(self.storage.read())
        audit_entries = self._load_audit_entries(events)
        report = self.emitter.generate(audit_entries)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.emitter.export_json(report, self.output_path)

        # Record metrics
        self.metrics.set("compliance.events.total", report.metrics.total_events)
        self.metrics.set("compliance.events.opted_in", report.metrics.opted_in_events)
        self.metrics.set("compliance.events.opt_out_blocked", report.metrics.opt_out_blocked)
        self.metrics.set("compliance.events.consent_unknown", report.metrics.consent_unknown)
        self.metrics.set("compliance.notices.total", len(report.notices))
        duration = perf_counter() - start
        self.metrics.observe("compliance.job.duration_seconds", duration)

        highlight = self._highlight_for(report)
        if self.atlas_service is not None:
            try:
                self.atlas_service.ensure_ready()
                self.atlas_service.append_highlight(highlight)
            except Exception:  # pragma: no cover - Atlas persistence is optional
                pass

        counters = {
            "compliance.events.total": report.metrics.total_events,
            "compliance.events.opted_in": report.metrics.opted_in_events,
            "compliance.events.opt_out_blocked": report.metrics.opt_out_blocked,
            "compliance.events.consent_unknown": report.metrics.consent_unknown,
            "compliance.notices.total": len(report.notices),
        }
        return AtlasJobResult(
            duration_seconds=duration,
            counters=counters,
            notices=report.notices,
            highlight=highlight,
            report_path=self.output_path,
        )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--telemetry",
        type=Path,
        default=DEFAULT_TELEMETRY_PATH,
        help="Path to the telemetry events JSONL file.",
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=None,
        help="Optional path to audit entries (JSON list).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Where to write the generated compliance report.",
    )
    parser.add_argument(
        "--metrics-out",
        type=Path,
        default=DEFAULT_METRICS_PATH,
        help="Where to write the Atlas metrics snapshot.",
    )
    parser.add_argument(
        "--atlas-root",
        type=Path,
        default=None,
        help="Atlas project root for persisting highlights.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    atlas_service = None
    if AtlasService is not None and args.atlas_root is not None:
        atlas_service = AtlasService(args.atlas_root)

    job = ComplianceAtlasJob(
        telemetry_path=args.telemetry,
        audit_path=args.audit,
        output_path=args.output,
        atlas_service=atlas_service,
    )
    result = job.execute()
    job.metrics.export(args.metrics_out)
    payload = {
        "duration_seconds": result.duration_seconds,
        "counters": dict(result.counters),
        "notices": list(result.notices),
        "highlight": result.highlight,
        "report_path": str(result.report_path),
        "metrics_path": str(args.metrics_out),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
