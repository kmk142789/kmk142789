from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import time

from echo.continuum_health import generate_continuum_health
from echo.echoctl import run_health


def _write(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_generate_continuum_health_missing(tmp_path):
    plan = tmp_path / "docs" / "NEXT_CYCLE_PLAN.md"
    manifest = tmp_path / "data" / "wish_manifest.json"
    pulses = tmp_path / "pulse_history.json"

    report = generate_continuum_health(plan, manifest, pulses)

    assert report.status == "critical"
    assert not report.plan_exists
    assert report.wish_total == 0
    assert report.pulse_count == 0
    assert any(issue.severity == "critical" for issue in report.issues)


def test_generate_continuum_health_healthy(tmp_path):
    plan = tmp_path / "docs" / "NEXT_CYCLE_PLAN.md"
    manifest = tmp_path / "data" / "wish_manifest.json"
    pulses = tmp_path / "pulse_history.json"

    _write(plan, "# Plan")
    now = time.time()
    os.utime(plan, (now, now))

    manifest_payload = {
        "version": "1.0.0",
        "wishes": [
            {
                "wisher": "Echo",
                "desire": "Maintain joy",
                "catalysts": ["listening"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "new",
            }
        ],
    }
    _write(manifest, json.dumps(manifest_payload))

    pulse_time = datetime.now(timezone.utc) - timedelta(hours=1)
    pulses_payload = [
        {"timestamp": pulse_time.timestamp(), "message": "pulse", "hash": "deadbeef"}
    ]
    _write(pulses, json.dumps(pulses_payload))

    report = generate_continuum_health(plan, manifest, pulses)

    assert report.status == "ok"
    assert report.plan_exists
    assert report.plan_age_hours is not None and report.plan_age_hours < 1
    assert report.wish_total == 1
    assert report.new_wish_total == 1
    assert report.pulse_count == 1
    assert report.last_pulse_age_hours is not None and report.last_pulse_age_hours >= 0
    assert not report.issues


def test_run_health_warning_exit(tmp_path, capsys):
    plan = tmp_path / "plan.md"
    manifest = tmp_path / "wish.json"
    pulses = tmp_path / "pulses.json"

    _write(plan, "# Plan")
    old_time = time.time() - 100 * 3600
    os.utime(plan, (old_time, old_time))

    manifest_payload = {"version": "1.0.0", "wishes": []}
    _write(manifest, json.dumps(manifest_payload))

    pulses_payload = []
    _write(pulses, json.dumps(pulses_payload))

    code = run_health(
        [
            "--plan",
            str(plan),
            "--manifest",
            str(manifest),
            "--pulses",
            str(pulses),
            "--fail-on-warning",
        ]
    )

    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert code == 1
