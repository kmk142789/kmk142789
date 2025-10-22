from __future__ import annotations

import json

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
