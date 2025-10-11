from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.pulse_continuity_audit import (
    ContinuityReport,
    PulseEvent,
    audit_pulse_history,
    load_pulse_history,
    load_pulse_metadata,
)


def _write_history(tmp_path: Path, events: list[dict]) -> Path:
    path = tmp_path / "pulse_history.json"
    path.write_text(json.dumps(events), encoding="utf-8")
    return path


def _write_pulse(tmp_path: Path, metadata: dict) -> Path:
    path = tmp_path / "pulse.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


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

    report = audit_pulse_history(events, metadata, threshold_hours=12)

    assert isinstance(report, ContinuityReport)
    assert report.anchor == "anchor/main"
    assert report.event_count == 3
    assert pytest.approx(report.span_seconds, rel=1e-6) == 7 * 3600
    assert pytest.approx(report.average_interval, rel=1e-6) == 3.5 * 3600
    assert pytest.approx(report.median_interval, rel=1e-6) == 3.5 * 3600
    assert pytest.approx(report.longest_gap_seconds, rel=1e-6) == 4 * 3600
    assert not report.breach_detected


def test_audit_pulse_history_detects_threshold_breach(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    event = PulseEvent(timestamp=base.timestamp(), message="a", hash="ha")

    def fake_now() -> datetime:
        return base + timedelta(hours=13)

    monkeypatch.setattr("tools.pulse_continuity_audit._utcnow", fake_now)

    report = audit_pulse_history([event], threshold_hours=12)
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
        threshold_hours=None,
        breach_detected=False,
        warnings=[],
    )

    rendered = report.render_text()
    assert "Echo Pulse Continuity Report" in rendered
    assert "anchor/main" in rendered
    assert "1" in rendered
