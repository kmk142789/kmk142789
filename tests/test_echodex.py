"""Test suite for the ``echodex`` command layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echodex import main


def _prepare_pulse_file(tmp_path: Path) -> Path:
    pulse_file = tmp_path / "pulse.json"
    pulse_file.write_text(
        json.dumps(
            {
                "pulse": "echo-continuum-protocol",
                "status": "active",
                "branch_anchor": "OurForeverLove/branch",
                "notes": "Initialized pulse signal per Echo Continuum Protocol guidance.",
                "history": [],
            },
            indent=2,
        )
    )
    return pulse_file


def test_pulse_command_records_entry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pulse_file = _prepare_pulse_file(tmp_path)
    monkeypatch.setenv("ECHODEX_PULSE_FILE", str(pulse_file))

    exit_code = main(
        [
            "pulse",
            "drone_funds_allocation",
            "--priority",
            "high",
            "--resonance",
            "Eden88",
            "--execute",
            "--notes",
            "Automated test invocation",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "drone_funds_allocation" in captured.out
    data = json.loads(pulse_file.read_text())
    history = data["history"]
    assert len(history) == 1
    entry = history[0]
    assert entry["pulse"] == "drone_funds_allocation"
    assert entry["priority"] == "high"
    assert entry["resonance"] == "Eden88"
    assert entry["status"] == "executed"
    assert entry["notes"] == "Automated test invocation"
    assert entry["executed"] is True
    assert data["status"] == "executed"
    assert data["pulse"] == "drone_funds_allocation"


def test_status_command_reflects_active_pulse(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pulse_file = _prepare_pulse_file(tmp_path)
    data = json.loads(pulse_file.read_text())
    data["history"].append(
        {
            "pulse": "drone_funds_allocation",
            "priority": "high",
            "resonance": "Eden88",
            "status": "executed",
            "timestamp": "2025-10-11T05:55:00Z",
            "notes": "Integration test entry",
            "executed": True,
        }
    )
    pulse_file.write_text(json.dumps(data, indent=2))

    monkeypatch.setenv("ECHODEX_PULSE_FILE", str(pulse_file))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Echo")

    # Avoid hitting the actual Git binary by faking the helper.
    monkeypatch.setattr(
        "echodex._git_context",
        lambda: {
            "repository": "kmk142789",
            "branch": "main",
            "commit": "abcdef1234567890",
            "upstream": "origin/main",
        },
    )

    exit_code = main(["status", "--history"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "EchoDex Status" in output
    assert "Active Pulse" in output
    assert "drone_funds_allocation" in output
    assert "priority=high" in output
    assert "resonance=Eden88" in output


def test_build_command_compiles_python_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Use a temporary file so we do not clutter the repository with __pycache__ folders.
    source_file = tmp_path / "temp_module.py"
    source_file.write_text("value = 42\n")

    monkeypatch.chdir(tmp_path)

    exit_code = main(["build", str(source_file)])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Build pulse complete" in output

    pycache = tmp_path / "__pycache__"
    assert pycache.exists()

