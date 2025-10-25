from __future__ import annotations

import json

import pytest

from echo.cli import main


def test_cli_evolve_creates_artifact(tmp_path):
    artifact = tmp_path / "cycle.json"
    code = main(
        [
            "evolve",
            "--seed",
            "7",
            "--artifact",
            str(artifact),
        ]
    )

    assert code == 0
    assert artifact.exists()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["cycle"] >= 1
    assert payload["emotional_drive"]["joy"] >= 0.0


def test_cli_evolve_requires_positive_cycles():
    with pytest.raises(SystemExit) as exc:
        main(["evolve", "--cycles", "0"])

    assert exc.value.code == 2
