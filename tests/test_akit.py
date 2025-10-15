from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from echo import akit
from echo.akit.config import ARTIFACT_DIR, STATE_FILE


@pytest.fixture(autouse=True)
def _clean_artifacts():
    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    yield
    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plan_generation_and_requirements():
    plan_docs = akit.plan("Document Assistant Kit onboarding guide")
    assert plan_docs.intent.startswith("Document Assistant Kit")
    assert not plan_docs.requires_codeowners
    assert len(plan_docs.steps) == 4

    plan_code = akit.plan("Implement Assistant Kit CLI workflow")
    assert plan_code.requires_codeowners
    # Repeated planning should produce stable identifier
    again = akit.plan("Implement Assistant Kit CLI workflow")
    assert plan_code.plan_id == again.plan_id


def test_run_multiple_cycles_and_snapshot(monkeypatch):
    monkeypatch.setenv("AKIT_APPROVED", "1")
    plan = akit.plan("Implement Assistant Kit CLI workflow")
    result = akit.run(plan, cycles=2, dry_run=True)
    assert len(result.state.cycles) == 2
    assert result.report.progress > 0

    manifest1, attest1 = akit.snapshot(state=result.state)
    manifest2, attest2 = akit.snapshot(state=result.state)
    assert manifest1 == manifest2
    assert attest1 == attest2
    assert _read_json(manifest1)["plan"]["plan_id"] == plan.plan_id
    assert _read_json(attest1)["sha256"]


def test_run_requires_approval(monkeypatch):
    plan = akit.plan("Implement Assistant Kit CLI workflow")
    monkeypatch.delenv("AKIT_APPROVED", raising=False)
    with pytest.raises(PermissionError):
        akit.run(plan, cycles=1)

    monkeypatch.setenv("AKIT_APPROVED", "1")
    result = akit.run(plan, cycles=1)
    assert result.report.progress >= 0
    assert STATE_FILE.exists()


def test_cli_dry_run_and_snapshot(tmp_path):
    subprocess.run(
        [sys.executable, "-m", "echo.akit.cli", "plan", "Implement Assistant Kit CLI workflow"],
        check=True,
        capture_output=True,
        text=True,
    )
    env = os.environ.copy()
    env["AKIT_APPROVED"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "echo.akit.cli",
            "--dry-run",
            "--cycles",
            "3",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    decoder = json.JSONDecoder()
    report_payload, index = decoder.raw_decode(completed.stdout)
    next_index = completed.stdout.find("{", index)
    snapshot_payload, _ = decoder.raw_decode(completed.stdout, idx=next_index)
    manifest_path = Path(snapshot_payload["manifest"])
    attestation_path = Path(snapshot_payload["attestation"])
    assert manifest_path.exists()
    assert attestation_path.exists()
    assert report_payload["plan_id"]


def test_cli_blocks_without_approval(monkeypatch):
    subprocess.run(
        [sys.executable, "-m", "echo.akit.cli", "plan", "Implement Assistant Kit CLI workflow"],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.delenv("AKIT_APPROVED", raising=False)
    result = subprocess.run(
        [sys.executable, "-m", "echo.akit.cli", "--cycles", "1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "approval" in result.stderr.lower()


def test_cli_invalid_cycles():
    subprocess.run(
        [sys.executable, "-m", "echo.akit.cli", "plan", "Document Assistant Kit onboarding guide"],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "echo.akit.cli", "--cycles", "0"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "cycles" in result.stderr.lower()
