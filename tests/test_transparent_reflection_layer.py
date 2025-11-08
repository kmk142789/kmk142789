from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from pulse_dashboard import WorkerHive
from services.universal_verifier import app as universal_app
from services.universal_verifier.app import _stats, _stats_lock
from src.reflection import ReflectionMetric, ReflectionTrace, TransparentReflectionLayer
from src.telemetry.collector import TelemetryCollector
from src.telemetry.schema import ConsentState, TelemetryContext
from src.telemetry.storage import InMemoryTelemetryStorage

from reports.data.reflection_transparency import (
    build_reflection_report,
    load_reflection_diagnostics,
    summarise_reflection_metrics,
)


def test_transparent_reflection_layer_records_telemetry() -> None:
    storage = InMemoryTelemetryStorage()
    collector = TelemetryCollector(storage=storage, metadata={"session_label": "tests"})
    context = TelemetryContext.pseudonymize(
        raw_identifier="unit-test-user@example.com",
        salt="reflection",
        consent_state=ConsentState.OPTED_IN,
    )
    layer = TransparentReflectionLayer(
        component="tests.component",
        collector=collector,
        context=context,
    )

    payload = layer.emit(
        metrics=[ReflectionMetric(key="events", value=1)],
        traces=[ReflectionTrace(event="tests.event", detail={"status": "ok"})],
        safeguards=["no_personal_data_logged"],
        diagnostics={"source": "unit"},
    )

    assert payload["component"] == "tests.component"
    events = list(storage.read())
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "reflection.snapshot"
    assert "name" not in event.payload


def test_worker_hive_reflection_emits_snapshot(tmp_path: Path) -> None:
    hive = WorkerHive(project_root=tmp_path)
    snapshot = hive.reflection(
        "tests.worker",
        metrics=[{"key": "steps", "value": 2}],
        traces=[{"event": "tests.worker.completed", "detail": {"status": "ok"}}],
        safeguards=["no_personal_data_logged"],
        diagnostics={"artifact": "demo"},
    )

    assert snapshot["component"] == "tests.worker"
    log_path = tmp_path / "state" / "pulse_dashboard" / "worker_events.jsonl"
    assert log_path.exists()
    contents = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert any("\"status\": \"reflection\"" in line for line in contents)


def test_universal_verifier_reflection_endpoint_reports_metrics() -> None:
    client = TestClient(universal_app.app)
    with _stats_lock:
        _stats["total"] = 0
        _stats["failed"] = 0

    client.post("/verify", json={"format": "jwt-vc", "credential": {"foo": "bar"}})
    client.post("/verify", json={"format": "jwt-vc", "credential": None})

    response = client.get("/reflection")
    assert response.status_code == 200
    payload = response.json()
    metrics = {item["key"]: item["value"] for item in payload["metrics"]}
    assert metrics["requests_total"] >= 2
    assert metrics["requests_failed"] >= 1
    assert "transparent_reflection_layer_enabled" in payload["safeguards"]
    assert "name" not in payload["diagnostics"]


def test_reflection_pipeline_builds_report(tmp_path: Path) -> None:
    history_path = tmp_path / "pulse_history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "reflection": {
                        "component": "tests.pipeline",
                        "metrics": {"workers": 2},
                        "safeguards": ["no_personal_data_logged"],
                    }
                }
            ]
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "reports" / "data" / "reflection.json"
    report = build_reflection_report(
        pulse_history_path=history_path,
        output_path=output_path,
    )
    assert output_path.exists()
    diagnostics = load_reflection_diagnostics(history_path)
    summary = summarise_reflection_metrics(diagnostics)
    assert report["snapshot"] == summary
    assert summary["components"] == 1
    assert summary["metrics"]["workers"] == 2.0
