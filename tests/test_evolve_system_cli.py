from __future__ import annotations

import json

import pytest

from scripts import evolve_system


def test_evolve_system_cli_runs_full_cycle(tmp_path, capsys):
    artifact = tmp_path / "cycle.json"

    exit_code = evolve_system.main([
        "--seed",
        "7",
        "--artifact",
        str(artifact),
    ])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Cycle Evolved" in captured.out

    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["cycle"] == 1
    assert data["glyphs"].startswith("∇")


def test_evolve_system_cli_runs_multiple_cycles(tmp_path, capsys):
    artifact = tmp_path / "cycles.json"

    exit_code = evolve_system.main([
        "--seed",
        "3",
        "--artifact",
        str(artifact),
        "--cycles",
        "3",
    ])

    assert exit_code == 0
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["cycle"] == 3


def test_evolve_system_cli_respects_no_persist(tmp_path):
    artifact = tmp_path / "skip.json"

    exit_code = evolve_system.main([
        "--seed",
        "11",
        "--artifact",
        str(artifact),
        "--no-persist-artifact",
    ])

    assert exit_code == 0
    assert artifact.exists() is False


def test_evolve_system_cli_rejects_invalid_cycle_count():
    with pytest.raises(SystemExit) as excinfo:
        evolve_system.main(["--cycles", "0"])

    assert excinfo.value.code == 2
