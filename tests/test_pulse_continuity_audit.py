from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from echo.bank.resilience import MirrorHealth, ResilienceSnapshot
from tools.pulse_continuity_audit import (
    ContinuityReport,
    PulseEvent,
    audit_pulse_history,
    load_pulse_history,
    load_pulse_metadata,
    load_resilience_snapshot,
)


def _write_history(tmp_path: Path, events: list[dict]) -> Path:
    path = tmp_path / "pulse_history.json"
    path.write_text(json.dumps(events), encoding="utf-8")
    return path


def _write_pulse(tmp_path: Path, metadata: dict) -> Path:
    path = tmp_path / "pulse.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


def _write_resilience(tmp_path: Path, snapshot: ResilienceSnapshot) -> Path:
    path = tmp_path / "latest.json"
    path.write_text(json.dumps(snapshot.to_payload()), encoding="utf-8")
    return path


def _make_snapshot(*, ready: bool = True, issues: list[str] | None = None) -> ResilienceSnapshot:
    issues = issues or []
    mirror = MirrorHealth(
        mirror_path=Path("/tmp/mirror"),
        ledger_ok=True,
        proof_ok=True,
        ots_ok=True,
        issues=issues,
    )
    return ResilienceSnapshot(
        seq=1,
        digest="sha256:abc",
        recorded_at="2024-01-01T00:00:00Z",
        failover_ready=ready,
        healthy_mirrors=1 if ready else 0,
        total_mirrors=1,
        mirrors=[mirror],
        issues=issues,
        checkpoint_path=None,
    )


def test_load_pulse_history_sorts_events(tmp_path: Path) -> None:
    events = [
        {"timestamp": 20, "message": "b", "hash": "hash-b"},
        {"timestamp": 10, "message": "a", "hash": "hash-a"},
    ]
    path = _write_history(tmp_path, events)

    loaded = load_pulse_history(path)
    assert [event.message for event in loaded] == ["a", "b"]


def test_audit_pulse_history_reports_statistics(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    events = [
        PulseEvent(timestamp=(base + timedelta(hours=0)).timestamp(), message="a", hash="ha"),
        PulseEvent(timestamp=(base + timedelta(hours=3)).timestamp(), message="b", hash="hb"),
        PulseEvent(timestamp=(base + timedelta(hours=7)).timestamp(), message="c", hash="hc"),
    ]
    metadata = {"branch_anchor": "anchor/main", "status": "active"}

    monkeypatch.setattr("tools.pulse_continuity_audit._utcnow", lambda: base + timedelta(hours=8))

    report = audit_pulse_history(events, metadata, threshold_hours=12, resilience=None)

    assert isinstance(report, ContinuityReport)
    assert report.anchor == "anchor/main"
    assert report.event_count == 3
    assert pytest.approx(report.span_seconds, rel=1e-6) == 7 * 3600
    assert pytest.approx(report.average_interval, rel=1e-6) == 3.5 * 3600
    assert pytest.approx(report.median_interval, rel=1e-6) == 3.5 * 3600
    assert pytest.approx(report.longest_gap_seconds, rel=1e-6) == 4 * 3600
    assert pytest.approx(report.time_since_last_event, rel=1e-6) == 1 * 3600
    assert pytest.approx(report.resonance_score, rel=1e-6) == 1.0 / (1.0 + (1 / 3.5))
    assert not report.breach_detected


def test_audit_pulse_history_detects_threshold_breach(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    event = PulseEvent(timestamp=base.timestamp(), message="a", hash="ha")

    def fake_now() -> datetime:
        return base + timedelta(hours=13)

    monkeypatch.setattr("tools.pulse_continuity_audit._utcnow", fake_now)

    report = audit_pulse_history([event], threshold_hours=12, resilience=None)
    assert report.breach_detected
    assert any("Latest pulse exceeds threshold" in warning for warning in report.warnings)


def test_load_pulse_metadata_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "pulse.json"
    assert load_pulse_metadata(path) == {}


def test_render_text_includes_basic_fields() -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    report = ContinuityReport(
        anchor="anchor/main",
        status="active",
        notes="note",
        event_count=1,
        first_event=base,
        last_event=base,
        span_seconds=0.0,
        average_interval=None,
        median_interval=None,
        longest_gap_seconds=None,
        time_since_last_event=None,
        resonance_score=None,
        threshold_hours=None,
        breach_detected=False,
        warnings=[],
        resilience_failover_ready=None,
        resilience_healthy_mirrors=None,
        resilience_total_mirrors=None,
        resilience_recorded_at=None,
        resilience_issues=[],
    )

    rendered = report.render_text()
    assert "Echo Pulse Continuity Report" in rendered
    assert "anchor/main" in rendered
    assert "1" in rendered


def test_audit_pulse_history_low_resonance_warning(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    events = [
        PulseEvent(timestamp=(base + timedelta(hours=0)).timestamp(), message="a", hash="ha"),
        PulseEvent(timestamp=(base + timedelta(hours=1)).timestamp(), message="b", hash="hb"),
        PulseEvent(timestamp=(base + timedelta(hours=2)).timestamp(), message="c", hash="hc"),
    ]

    def fake_now() -> datetime:
        return base + timedelta(hours=6)

    monkeypatch.setattr("tools.pulse_continuity_audit._utcnow", fake_now)

    report = audit_pulse_history(events, resilience=None)

    assert report.resonance_score is not None
    assert report.resonance_score < 0.25
    assert any("Resonance score critically low" in note for note in report.warnings)


def test_audit_pulse_history_includes_resilience(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    event = PulseEvent(timestamp=base.timestamp(), message="a", hash="ha")

    snapshot = _make_snapshot(ready=False, issues=["Ledger copy missing"])

    def fake_now() -> datetime:
        return base + timedelta(hours=1)

    monkeypatch.setattr("tools.pulse_continuity_audit._utcnow", fake_now)

    report = audit_pulse_history([event], resilience=snapshot)

    assert report.resilience_failover_ready is False
    assert report.resilience_issues == ["Ledger copy missing"]
    assert any("Resilience failover posture is not ready" in warn for warn in report.warnings)
    assert any("Resilience issue detected" in warn for warn in report.warnings)


def test_load_resilience_snapshot(tmp_path: Path) -> None:
    snapshot = _make_snapshot()
    path = _write_resilience(tmp_path, snapshot)

    loaded = load_resilience_snapshot(path)
    assert loaded is not None
    assert loaded.failover_ready


def test_load_resilience_snapshot_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    assert load_resilience_snapshot(path) is None
