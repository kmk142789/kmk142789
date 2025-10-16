from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ECHOCTL = ROOT / "echo" / "echoctl.py"
DATA = ROOT / "data" / "wish_manifest.json"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ECHOCTL), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
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
