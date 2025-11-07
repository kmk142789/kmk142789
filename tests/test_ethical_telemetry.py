from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.self_assessment import ReportEmitter
from src.self_assessment.metrics import ComplianceEvaluator
from src.telemetry import (
    ConsentState,
    TelemetryCollector,
    TelemetryContext,
    TelemetryEvent,
)
from src.telemetry.storage import InMemoryTelemetryStorage, JsonlTelemetryStorage
from tools.telemetry_review import (
    build_audit_entries,
    create_report,
    ensure_secure_transport,
)


def test_pseudonymized_context_consistency() -> None:
    ctx_a = TelemetryContext.pseudonymize(
        raw_identifier="user-123",
        salt="salty",
        consent_state=ConsentState.OPTED_IN,
        consent_recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    ctx_b = TelemetryContext.pseudonymize(
        raw_identifier="user-123",
        salt="salty",
        consent_state=ConsentState.OPTED_IN,
        consent_recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert ctx_a.pseudonymous_id == ctx_b.pseudonymous_id
    assert ctx_a.consent_state is ConsentState.OPTED_IN


def test_telemetry_event_rejects_sensitive_payload() -> None:
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-456",
        salt="salty",
        consent_state=ConsentState.OPTED_IN,
    )
    with pytest.raises(ValueError):
        TelemetryEvent(event_type="signup", context=ctx, payload={"email": "test@example"})


def test_collector_respects_consent() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage)
    ctx_in = TelemetryContext.pseudonymize(
        raw_identifier="user-in",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )
    ctx_out = TelemetryContext.pseudonymize(
        raw_identifier="user-out",
        salt="salt",
        consent_state=ConsentState.OPTED_OUT,
    )
    collector.record(event_type="visit", context=ctx_in, payload={"action": "view"})
    collector.record(event_type="visit", context=ctx_out, payload={"action": "view"})
    events = list(storage.read())
    assert len(events) == 1
    assert events[0].payload == {"action": "view"}
    assert events[0].context.pseudonymous_id == ctx_in.pseudonymous_id


def test_compliance_evaluator_metrics() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage)
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-789",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )
    collector.record(event_type="action", context=ctx, payload={"step": "complete"})
    metrics = ComplianceEvaluator().compute(storage.read())
    assert metrics.total_events == 1
    assert metrics.opt_in_ratio == pytest.approx(1.0)


def test_report_emitter_generates_report(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    storage = JsonlTelemetryStorage(events_path)
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-abc",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )
    event = TelemetryEvent(event_type="progress", context=ctx, payload={"level": 3})
    storage.write(event)

    report_path = tmp_path / "report.json"
    report = create_report(events_path, audit_path=None, output_path=report_path)
    assert report_path.exists()
    assert report["metrics"]["total_events"] == 1

    emitter = ReportEmitter(storage=storage)
    final_report = emitter.generate(build_audit_entries([event.model_dump()]))
    assert final_report.metrics.total_events == 1
    assert not final_report.notices


def test_secure_transport_validation() -> None:
    ensure_secure_transport("https://example.com/telemetry")
    with pytest.raises(ValueError):
        ensure_secure_transport("http://example.com/telemetry")
