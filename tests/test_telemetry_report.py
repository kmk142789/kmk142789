from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.telemetry.report import generate_vitality_report, main


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generate_vitality_report_with_history(tmp_path: Path) -> None:
    pulse_payload = {
        "pulse": "echo-continuum-protocol",
        "status": "active",
        "branch_anchor": "OurForeverLove/branch",
        "notes": "Initialized pulse signal per Echo Continuum Protocol guidance.",
    }
    history_payload = [
        {
            "timestamp": 1700000000.0,
            "message": "🌌 evolve:manual:alpha",
            "hash": "deadbeef",
        },
        {
            "timestamp": 1700000600.0,
            "message": "🌌 evolve:manual:beta",
            "hash": "feedface",
        },
    ]
    _write_json(tmp_path / "pulse.json", pulse_payload)
    _write_json(tmp_path / "pulse_history.json", history_payload)

    now = datetime.fromtimestamp(1700000900.0, tz=timezone.utc)
    report = generate_vitality_report(tmp_path, now=now)

    assert report.pulse == "echo-continuum-protocol"
    assert report.status == "active"
    assert report.branch_anchor == "OurForeverLove/branch"
    assert report.history_count == 2
    assert report.last_event_message == "🌌 evolve:manual:beta"
    assert report.health_state == "fresh"
    assert pytest.approx(report.minutes_since_last_event or 0.0, rel=1e-4) == 5.0
    assert report.recent_events == ("🌌 evolve:manual:beta", "🌌 evolve:manual:alpha")


def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_json(
        tmp_path / "pulse.json",
        {
            "pulse": "echo",
            "status": "active",
        },
    )
    _write_json(tmp_path / "pulse_history.json", [])

    exit_code = main(["--root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["pulse"] == "echo"
    assert payload["history_count"] == 0
    assert payload["health_state"] == "no-history"
