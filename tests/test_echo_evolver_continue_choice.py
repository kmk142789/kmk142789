import pytest

from echo.evolver import EchoEvolver


def test_continue_choice_completes_pending_steps(tmp_path):
    artifact_path = tmp_path / "pending.json"
    evolver = EchoEvolver(artifact_path=artifact_path)

    evolver.advance_cycle()
    evolver.mutate_code()

    payload = evolver.continue_choice(
        enable_network=False, persist_artifact=False, include_report=True
    )

    assert payload["decision"] == "continue_cycle"
    digest = payload["digest"]
    assert digest["remaining_steps"] == []
    assert digest["progress"] == pytest.approx(1.0)
    assert "report" in payload
    assert payload["report"].startswith("Cycle")
    assert "status" in payload
    assert payload["status"]["cycle"] == digest["cycle"]

    record = evolver.state.network_cache["continue_choice"]
    assert record["decision"] == "continue_cycle"
    assert record["remaining_steps"] == []
    assert "report" in record
    assert record["status"]["cycle"] == digest["cycle"]
    assert "continue_choice()" in evolver.state.event_log[-1]


def test_continue_choice_delegates_when_cycle_complete(tmp_path):
    artifact_path = tmp_path / "complete.json"
    evolver = EchoEvolver(artifact_path=artifact_path)

    evolver.run(enable_network=False, persist_artifact=False)

    payload = evolver.continue_choice(
        enable_network=False, persist_artifact=False, include_report=False
    )

    assert payload["decision"] == "continue_evolution"
    digest = payload["digest"]
    assert digest["remaining_steps"] == []
    assert "report" not in payload
    assert "status" in payload

    record = evolver.state.network_cache["continue_choice"]
    assert record["decision"] == "continue_evolution"
    assert record["remaining_steps"] == []
    assert "report" not in record
    assert "status" in record


def test_continue_choice_can_skip_status(tmp_path):
    artifact_path = tmp_path / "skip.json"
    evolver = EchoEvolver(artifact_path=artifact_path)

    payload = evolver.continue_choice(
        enable_network=False,
        persist_artifact=False,
        include_report=False,
        include_status=False,
    )

    assert payload["decision"] == "continue_cycle"
    assert "status" not in payload

    record = evolver.state.network_cache["continue_choice"]
    assert "status" not in record
