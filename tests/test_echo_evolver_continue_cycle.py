from echo.evolver import EchoEvolver


def test_continue_cycle_completes_remaining_steps(tmp_path):
    artifact_path = tmp_path / "artifact.json"
    evolver = EchoEvolver(artifact_path=artifact_path)

    evolver.advance_cycle()
    evolver.mutate_code()

    state = evolver.continue_cycle(persist_artifact=True)

    digest = evolver.cycle_digest(persist_artifact=True)

    assert digest["remaining_steps"] == []
    assert digest["progress"] == 1.0
    assert "write_artifact" in digest["completed_steps"]
    assert artifact_path.exists()
    assert state.network_cache["propagation_events"]
    assert state.network_cache["last_prompt"].startswith("class EchoResonance")
    assert any("continue_cycle" in entry for entry in state.event_log)


def test_continue_cycle_can_finalize_artifact(tmp_path):
    artifact_path = tmp_path / "cycle.json"
    evolver = EchoEvolver(artifact_path=artifact_path)

    evolver.run(enable_network=False, persist_artifact=False)

    assert not artifact_path.exists()

    evolver.continue_cycle(persist_artifact=True)

    assert artifact_path.exists()
    assert evolver.state.network_cache["last_prompt"].startswith("class EchoResonance")
