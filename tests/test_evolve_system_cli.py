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


def test_evolve_system_cli_prints_artifact_payload(tmp_path, capsys):
    artifact = tmp_path / "print.json"

    exit_code = evolve_system.main([
        "--seed",
        "13",
        "--artifact",
        str(artifact),
        "--no-persist-artifact",
        "--print-artifact",
    ])

    assert exit_code == 0
    assert artifact.exists() is False

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    json_start = next(i for i, line in enumerate(lines) if line.lstrip().startswith("{"))
    payload = json.loads("\n".join(lines[json_start:]))

    assert payload["cycle"] == 1
    assert payload["prompt"]["title"] == "Echo Resonance"


def test_evolve_system_cli_advances_system(tmp_path, capsys):
    artifact = tmp_path / "advance.json"

    exit_code = evolve_system.main([
        "--seed",
        "17",
        "--artifact",
        str(artifact),
        "--advance-system",
        "--print-artifact",
        "--include-event-summary",
        "--include-matrix",
    ])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Cycle" in output and "advanced" in output
    lines = output.splitlines()
    json_start = next(
        idx
        for idx, line in enumerate(lines)
        if line.lstrip() == "{" and idx + 1 < len(lines) and '"cycle"' in lines[idx + 1]
    )
    data = json.loads("\n".join(lines[json_start:]))
    assert data["cycle"] == 1
    assert "event_summary" in data
    assert "progress_matrix" in data
    assert artifact.exists()


def test_evolve_system_cli_rejects_invalid_advance_flags():
    with pytest.raises(SystemExit) as excinfo:
        evolve_system.main(["--include-matrix"])

    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        evolve_system.main([
            "--advance-system",
            "--include-system-report",
            "--system-report-events",
            "0",
        ])

    assert excinfo.value.code == 2
