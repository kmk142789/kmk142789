from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import json
import pytest

from src.telemetry.audit import (
    ConsentComplianceError,
    ConsentComplianceReport,
    generate_compliance_report,
    main,
)
from src.telemetry.schema import ConsentState, TelemetryContext, TelemetryEvent
from src.telemetry.storage import JsonlTelemetryStorage


def _write_events(path: Path) -> None:
    storage = JsonlTelemetryStorage(path)

    context_in = TelemetryContext(
        id="0123456789abcdef",
        consent_state=ConsentState.OPTED_IN,
        consent_recorded_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    event_in = TelemetryEvent(
        event_type="pulse.launch",
        occurred_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        context=context_in,
        payload={"metric": 1},
    )
    storage.write(event_in)

    context_out = TelemetryContext(
        id="fedcba9876543210",
        consent_state=ConsentState.OPTED_OUT,
        consent_recorded_at=datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc),
    )
    event_out = TelemetryEvent(
        event_type="pulse.observe",
        occurred_at=datetime(2024, 1, 1, 12, 45, tzinfo=timezone.utc),
        context=context_out,
        payload={"metric": 2},
    )
    storage.write(event_out)


def test_generate_compliance_report(tmp_path: Path) -> None:
    log_path = tmp_path / "telemetry.jsonl"
    _write_events(log_path)

    now = datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc)
    report = generate_compliance_report(log_path, now=now)

    assert isinstance(report, ConsentComplianceReport)
    assert report.total_events == 2
    assert report.unique_sessions == 2
    assert report.consent_counts == {"opted_in": 1, "opted_out": 1}
    assert report.event_type_counts == {"pulse.launch": 1, "pulse.observe": 1}
    assert report.first_event_at == datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert report.last_event_at == datetime(2024, 1, 1, 12, 45, tzinfo=timezone.utc)
    assert report.non_opt_in_events == 1
    assert pytest.approx(report.minutes_active or 0.0, rel=1e-5) == 45.0
    assert pytest.approx(report.minutes_since_last_event or 0.0, rel=1e-5) == 15.0

    description = report.describe()
    assert "opted_out: 1" in description
    assert "Events recorded without opt-in consent: 1" in description

    serialised = report.as_dict()
    assert serialised["first_event_at"] == "2024-01-01T12:00:00Z"
    assert serialised["last_event_at"] == "2024-01-01T12:45:00Z"
    assert serialised["minutes_since_last_event"] == pytest.approx(15.0)


def test_generate_compliance_report_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(ConsentComplianceError):
        generate_compliance_report(missing)


def test_compliance_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log_path = tmp_path / "telemetry.jsonl"
    _write_events(log_path)

    exit_code = main([str(log_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["total_events"] == 2
    assert payload["consent_counts"]["opted_in"] == 1
    assert payload["consent_counts"]["opted_out"] == 1
