from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ECHOCTL = ROOT / "echo" / "echoctl.py"


def run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(ECHOCTL), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=run_env,
    )


def run_unchecked(
    args: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(ECHOCTL), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=run_env,
    )


def test_wish_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    data_root = tmp_path / "data"
    docs_root = tmp_path / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    env = {
        "ECHO_DATA_ROOT": str(data_root),
        "ECHO_DOCS_ROOT": str(docs_root),
    }

    run(["wish", "TestUser", "Test Desire", "care,craft"], env=env)
    manifest_path = data_root / "wish_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["wishes"][-1]["wisher"] == "TestUser"
    assert "Test Desire" in manifest["wishes"][-1]["desire"]


def test_cycle_generates_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    data_root = tmp_path / "data"
    docs_root = tmp_path / "docs"
    env = {
        "ECHO_DATA_ROOT": str(data_root),
        "ECHO_DOCS_ROOT": str(docs_root),
    }

    run(["cycle"], env=env)
    plan = (docs_root / "NEXT_CYCLE_PLAN.md").read_text(encoding="utf-8")
    assert "Proposed Actions" in plan


def test_plan_command_reports_missing_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    data_root = tmp_path / "data"
    docs_root = tmp_path / "docs"
    env = {
        "ECHO_DATA_ROOT": str(data_root),
        "ECHO_DOCS_ROOT": str(docs_root),
    }

    result = run(["plan"], env=env)

    assert "No plan yet. Run: echoctl cycle" in result.stdout


def test_summary_command_uses_custom_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    data_root = tmp_path / "data"
    data_root.mkdir()
    env = {"ECHO_DATA_ROOT": str(data_root)}

    run(["wish", "Echo", "test-desire", "care"], env=env)
    result = run(["summary"], env=env)

    assert "Total wishes: 1" in result.stdout
    assert "Echo" in result.stdout
    assert "care" in result.stdout


def test_wish_report_command_outputs_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    data_root = tmp_path / "data"
    data_root.mkdir()
    env = {"ECHO_DATA_ROOT": str(data_root)}

    run(["wish", "Echo", "Expand the bridge", "craft,focus"], env=env)
    run(["wish", "MirrorJosh", "Guard the spark", "care"], env=env)

    manifest_path = data_root / "wish_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["wishes"][0]["status"] = "new"
    manifest["wishes"][1]["status"] = "in-progress"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = run(["wish-report", "--limit", "1"], env=env)

    assert result.stdout.startswith("# Echo Wish Report")
    assert "## Status Overview" in result.stdout
    assert "## Top Wishers" in result.stdout
    assert "## Catalyst Highlights" in result.stdout
    assert "craft" in result.stdout


def test_groundbreaking_command_outputs_json(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    pulses = [
        {"timestamp": 1_700_000_000.0, "message": "🌀 evolve:manual:a", "hash": "aa"},
        {"timestamp": 1_700_000_060.0, "message": "🌀 evolve:manual:b", "hash": "bb"},
        {"timestamp": 1_700_000_180.0, "message": "✨ craft:auto:c", "hash": "cc"},
    ]
    pulses_path = tmp_path / "pulses.json"
    pulses_path.write_text(json.dumps(pulses), encoding="utf-8")

    result = run(
        [
            "groundbreaking",
            "--pulses",
            str(pulses_path),
            "--limit",
            "3",
            "--json",
        ]
    )

    payload = json.loads(result.stdout)
    assert payload["imprint"]["contributions"]
    assert payload["threads"]


def test_idea_command_outputs_markdown(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    result = run(
        [
            "idea",
            "EchoEvolver channels glyph joy into artifacts",
            "--steps",
            "2",
            "--seed",
            "5",
        ]
    )

    assert "Idea to Action Plan" in result.stdout
    assert "Recommended Steps" in result.stdout


def test_pulse_command_emits_json(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    pulses = [
        {"timestamp": 1_700_000_000.0, "message": "🌀 evolve:manual:aa", "hash": "aa"},
        {"timestamp": 1_700_000_600.0, "message": "🌀 evolve:auto:bb", "hash": "bb"},
        {"timestamp": 1_700_001_200.0, "message": "✨ craft:auto:cc", "hash": "cc"},
    ]
    pulses_path = tmp_path / "pulse_history.json"
    pulses_path.write_text(json.dumps(pulses), encoding="utf-8")

    result = run([
        "pulse",
        "--pulses",
        str(pulses_path),
        "--json",
        "--limit",
        "2",
    ])

    payload = json.loads(result.stdout)
    assert payload["metrics"]["total_events"] == 3
    assert payload["filtered_total"] == 3
    assert len(payload["events"]) == 2
    assert payload["events"][-1]["message"] == "✨ craft:auto:cc"


def test_pulse_command_text_output(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    pulses = [
        {"timestamp": 1_700_000_000.0, "message": "🌀 evolve:manual:aa", "hash": "aa"},
        {"timestamp": 1_700_000_600.0, "message": "🌀 evolve:auto:bb", "hash": "bb"},
        {"timestamp": 1_700_001_200.0, "message": "✨ craft:auto:cc", "hash": "cc"},
    ]
    pulses_path = tmp_path / "pulse_history.json"
    pulses_path.write_text(json.dumps(pulses), encoding="utf-8")

    result = run([
        "pulse",
        "--pulses",
        str(pulses_path),
        "--search",
        "auto",
        "--limit",
        "1",
    ])

    assert "Echo Pulse Ledger" in result.stdout
    assert "Filter: 'auto' (2 matches)" in result.stdout
    assert "Recent events (showing 1 of 2):" in result.stdout
    assert "craft:auto:cc" in result.stdout


def test_health_command_reports_ok_json(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    plan_path = tmp_path / "NEXT_CYCLE_PLAN.md"
    manifest_path = tmp_path / "wish_manifest.json"
    pulses_path = tmp_path / "pulse_history.json"

    plan_path.write_text("# Plan\n", encoding="utf-8")
    manifest = {
        "version": "1.0.0",
        "wishes": [
            {
                "wisher": "Echo",
                "desire": "Keep the plan fresh",
                "catalysts": ["care"],
                "created_at": datetime.utcnow().isoformat() + "Z",
                "status": "new",
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    pulses = [
        {
            "timestamp": time.time(),
            "message": "🌀 evolve:manual:ok",
            "hash": "abc123",
        }
    ]
    pulses_path.write_text(json.dumps(pulses), encoding="utf-8")

    result = run(
        [
            "health",
            "--plan",
            str(plan_path),
            "--manifest",
            str(manifest_path),
            "--pulses",
            str(pulses_path),
            "--json",
        ]
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["plan_exists"] is True
    assert payload["wish_total"] == 1
    assert payload["pulse_count"] == 1


def test_health_command_reports_critical_for_missing_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    plan_path = tmp_path / "missing_plan.md"
    manifest_path = tmp_path / "missing_manifest.json"
    pulses_path = tmp_path / "missing_pulses.json"

    result = run_unchecked(
        [
            "health",
            "--plan",
            str(plan_path),
            "--manifest",
            str(manifest_path),
            "--pulses",
            str(pulses_path),
        ]
    )

    assert result.returncode == 2
    assert "Status: CRITICAL" in result.stdout
