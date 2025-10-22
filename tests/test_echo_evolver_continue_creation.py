import random

import pytest

from echo.evolver import EchoEvolver


@pytest.fixture
def evolver(tmp_path):
    return EchoEvolver(rng=random.Random(3), artifact_path=tmp_path / "artifact.json")


def test_continue_creation_executes_creation_steps(evolver):
    payload = evolver.continue_creation(theme="aurora", persist_artifact=False)

    assert payload["decision"] == "continue_creation"
    assert payload["cycle"] == evolver.state.cycle == 1
    assert payload["executed_steps"][-1] == "eden88_create_artifact"

    creation = payload["creation"]
    assert creation is not None
    assert creation["theme"] == "aurora"

    digest = payload["digest"]
    assert digest["remaining_steps"][0] == "system_monitor"
    assert evolver.state.network_cache["continue_creation"]["creation"]["theme"] == "aurora"
    assert "Eden88 shaped" in payload["report"]


def test_continue_creation_refreshes_existing_cycle(evolver):
    first = evolver.continue_creation(persist_artifact=False)

    second = evolver.continue_creation(theme="quantum", persist_artifact=False)

    assert second["decision"] == "continue_creation"
    assert second["cycle"] == evolver.state.cycle == first["cycle"]
    assert second["executed_steps"] == ["eden88_create_artifact"]
    assert second["creation"]["theme"] == "quantum"

    record = evolver.state.network_cache["continue_creation"]
    assert record["creation"]["theme"] == "quantum"
