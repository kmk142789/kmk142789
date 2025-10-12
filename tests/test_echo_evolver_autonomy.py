import random

from echo.evolver import EchoEvolver


def test_evolver_decentralized_autonomy_records_manifesto():
    rng = random.Random(42)
    evolver = EchoEvolver(rng=rng)
    evolver.advance_cycle()

    decision = evolver.decentralized_autonomy()

    assert decision.ratified is True
    assert "cycle-1" in decision.proposal_id
    assert evolver.state.autonomy_decision["proposal_id"] == decision.proposal_id
    assert evolver.state.autonomy_manifesto.startswith("Proposal")
    assert "autonomy_consensus" in evolver.state.network_cache


def test_autonomy_included_in_artifact_payload(tmp_path):
    evolver = EchoEvolver(artifact_path=tmp_path / "artifact.json")
    evolver.advance_cycle()
    evolver.decentralized_autonomy()
    prompt = evolver.inject_prompt_resonance()
    path = evolver.write_artifact(prompt)

    payload = path.read_text(encoding="utf-8")
    assert "\"autonomy\"" in payload
    assert "manifesto" in payload
