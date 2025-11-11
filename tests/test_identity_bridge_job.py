from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from integrations.identity_bridge import ComplianceAtlasJob
from atlas.metrics import AtlasMetricsService
from src.telemetry.schema import ConsentState, TelemetryContext, TelemetryEvent
from src.telemetry.storage import JsonlTelemetryStorage


class DummyAtlasService:
    def __init__(self) -> None:
        self.highlights: list[str] = []

    def ensure_ready(self) -> None:  # pragma: no cover - trivial
        return None

    def append_highlight(self, text: str) -> None:
        self.highlights.append(text)


def _write_events(path: Path) -> None:
    storage = JsonlTelemetryStorage(path)
    ctx = TelemetryContext(
        id="a" * 16,
        consent_state=ConsentState.OPTED_IN,
        consent_recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    storage.write(
        TelemetryEvent(
            event_type="consent.granted",
            context=ctx,
            payload={"feature": "atlas_bridge"},
        )
    )
    storage.write(
        TelemetryEvent(
            event_type="consent.revoked",
            context=TelemetryContext(
                id="b" * 16,
                consent_state=ConsentState.OPTED_OUT,
                consent_recorded_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            ),
            payload={},
        )
    )


def test_compliance_job_generates_report(tmp_path: Path) -> None:
    telemetry_path = tmp_path / "events.jsonl"
    _write_events(telemetry_path)

    metrics = AtlasMetricsService()
    atlas = DummyAtlasService()
    output_path = tmp_path / "report.json"
    job = ComplianceAtlasJob(
        telemetry_path=telemetry_path,
        output_path=output_path,
        metrics_service=metrics,
        atlas_service=atlas,
    )

    result = job.execute()
    metrics_path = tmp_path / "metrics.json"
    metrics.export(metrics_path)

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metrics"]["total_events"] == 2
    assert "Opt-in ratio" in result.highlight
    assert atlas.highlights  # highlight persisted

    snapshot = metrics.snapshot()
    assert snapshot["counters"]["compliance.events.total"] == 2
    exported = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert exported["counters"]["compliance.events.opted_in"] == 1
