import random

from echo.evolver import EchoEvolver


def test_continue_evolution_bootstraps_cycle(tmp_path):
    artifact_path = tmp_path / "cycle.json"
    evolver = EchoEvolver(rng=random.Random(1), artifact_path=artifact_path)

    payload = evolver.continue_evolution(persist_artifact=True)

    digest = payload["digest"]
    assert digest["cycle"] == evolver.state.cycle
    assert digest["progress"] == 1.0
    assert digest["remaining_steps"] == []
    assert "report" in payload
    assert payload["report"].startswith("Cycle")
    assert artifact_path.exists()

    record = evolver.state.network_cache["continue_evolution"]
    assert record["cycle"] == digest["cycle"]
    assert record["progress"] == digest["progress"]
    assert record["remaining_steps"] == []
    assert "continue_evolution()" in evolver.state.event_log[-1]


def test_continue_evolution_respects_flags(tmp_path):
    artifact_path = tmp_path / "no_artifact.json"
    evolver = EchoEvolver(rng=random.Random(2), artifact_path=artifact_path)

    evolver.advance_cycle()
    evolver.mutate_code()

    payload = evolver.continue_evolution(persist_artifact=False, include_report=False)

    digest = payload["digest"]
    assert "report" not in payload
    assert artifact_path.exists() is False
    assert digest["remaining_steps"] == []

    record = evolver.state.network_cache["continue_evolution"]
    assert "report" not in record
    assert record["remaining_steps"] == []
    assert record["next_step"] == "Next step: advance_cycle() to begin a new orbit"

