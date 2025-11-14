from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


@pytest.fixture
def evolver(tmp_path) -> EchoEvolver:
    return EchoEvolver(rng=random.Random(11), artifact_path=tmp_path / "artifact.json")


def test_recover_creation_recalls_existing_cycle(evolver: EchoEvolver) -> None:
    evolver.advance_cycle()
    creation = evolver.eden88_create_artifact(theme="aurora")

    payload = evolver.recover_creation(cycle=creation["cycle"], include_report=False)

    assert payload["decision"] == "recover_creation"
    assert payload["status"] == "recalled"
    assert payload["creation"]["title"] == creation["title"]
    record = evolver.state.network_cache["recover_creation"]
    assert record["status"] == "recalled"


def test_recover_creation_synthesizes_missing_cycle(evolver: EchoEvolver) -> None:
    target_cycle = 3

    payload = evolver.recover_creation(
        cycle=target_cycle, theme="memory", include_report=True
    )

    assert payload["status"] == "recovered"
    creation = payload["creation"]
    assert creation["cycle"] == target_cycle
    assert creation["title"].startswith("Eden88 Recovery")
    assert any("forgot" in verse.lower() for verse in creation["verses"])
    assert any(entry["cycle"] == target_cycle for entry in evolver.state.eden88_creations)
