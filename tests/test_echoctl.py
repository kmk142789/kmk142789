from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ECHOCTL = ROOT / "echo" / "echoctl.py"
DATA = ROOT / "data" / "wish_manifest.json"


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


def test_wish_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    run(["wish", "TestUser", "Test Desire", "care,craft"])
    manifest = json.loads(DATA.read_text(encoding="utf-8"))
    assert manifest["wishes"][-1]["wisher"] == "TestUser"
    assert "Test Desire" in manifest["wishes"][-1]["desire"]


def test_cycle_generates_plan(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    run(["cycle"])
    plan = (ROOT / "docs" / "NEXT_CYCLE_PLAN.md").read_text(encoding="utf-8")
    assert "Proposed Actions" in plan


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
