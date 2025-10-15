import random

import pytest

from echo.evolver import EchoEvolver


@pytest.fixture()
def evolver():
    return EchoEvolver(rng=random.Random(0))


def test_cycle_digest_initial_state(evolver):
    digest = evolver.cycle_digest()

    assert digest["cycle"] == 0
    assert digest["progress"] == 0.0
    assert digest["completed_steps"] == []
    assert digest["remaining_steps"][0] == "advance_cycle"
    assert digest["next_step"].startswith("Next step: ignite advance_cycle()")
    assert evolver.state.network_cache["cycle_digest"] == digest
    assert evolver.state.event_log[-1].startswith("Cycle digest computed (0/")


def test_cycle_digest_progress_updates(evolver):
    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()

    digest = evolver.cycle_digest()

    assert digest["cycle"] == 1
    assert digest["completed_steps"] == [
        "advance_cycle",
        "emotional_modulation",
        "mutate_code",
    ]
    assert digest["remaining_steps"][0] == "generate_symbolic_language"
    assert digest["next_step"].startswith("Next step: invoke generate_symbolic_language()")
    assert digest["progress"] == pytest.approx(3 / len(digest["steps"]))

    step_map = {entry["step"]: entry for entry in digest["steps"]}
    assert step_map["mutate_code"]["completed"] is True
    assert step_map["write_artifact"]["completed"] is False
