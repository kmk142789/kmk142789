from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.self_assessment import ReportEmitter
from src.self_assessment.metrics import ComplianceEvaluator
from src.telemetry import (
    ConsentState,
    PendingTelemetryEvent,
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


def test_collector_session_annotation() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage, metadata={"session_label": "beta"})
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-session",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )

    event = collector.record(event_type="visit", context=ctx, payload={})
    assert event is not None
    assert event.context.session_label == "beta"


def test_collector_record_batch_handles_mixed_events() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage)
    ctx_in = TelemetryContext.pseudonymize(
        raw_identifier="user-batch-in",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )
    ctx_out = TelemetryContext.pseudonymize(
        raw_identifier="user-batch-out",
        salt="salt",
        consent_state=ConsentState.OPTED_OUT,
    )

    recorded = collector.record_batch(
        [
            PendingTelemetryEvent(
                event_type="batch",  # allowed event
                context=ctx_in,
                payload={"action": "view", "debug": True},
                allowed_fields={"action"},
            ),
            PendingTelemetryEvent(
                event_type="batch",
                context=ctx_out,
                payload={"action": "skip"},
            ),
        ]
    )

    assert len(recorded) == 1
    assert recorded[0].payload == {"action": "view"}
    assert recorded[0].context.pseudonymous_id == ctx_in.pseudonymous_id


def test_collector_applies_default_allowed_fields() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(
        storage=storage, default_allowed_fields={"action", "label"}
    )
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-default", salt="salt", consent_state=ConsentState.OPTED_IN
    )

    event = collector.record(
        event_type="visit", context=ctx, payload={"action": "view", "debug": True}
    )

    assert event is not None
    assert event.payload == {"action": "view"}


def test_collector_rejects_oversized_payload() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage, max_payload_bytes=32)
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-large", salt="salt", consent_state=ConsentState.OPTED_IN
    )

    with pytest.raises(ValueError):
        collector.record(
            event_type="visit",
            context=ctx,
            payload={"action": "view", "details": "x" * 40},
        )


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


def test_jsonl_storage_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    storage = JsonlTelemetryStorage(path)
    ctx = TelemetryContext.pseudonymize(
        raw_identifier="user-blank",
        salt="salt",
        consent_state=ConsentState.OPTED_IN,
    )
    event = TelemetryEvent(event_type="visit", context=ctx, payload={"action": "view"})
    storage.write(event)

    path.write_text(path.read_text(encoding="utf-8") + "\n\n  \n", encoding="utf-8")

    events = list(storage.read())
    assert len(events) == 1
    assert events[0].event_type == "visit"


def test_secure_transport_validation() -> None:
    ensure_secure_transport("https://example.com/telemetry")
    with pytest.raises(ValueError):
        ensure_secure_transport("http://example.com/telemetry")
