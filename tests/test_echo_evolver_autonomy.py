import json
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


def test_artifact_payload_matches_written_file(tmp_path):
    evolver = EchoEvolver(artifact_path=tmp_path / "artifact.json")
    evolver.advance_cycle()
    evolver.emotional_modulation()
    evolver.generate_symbolic_language()
    evolver.system_monitor()
    prompt = evolver.inject_prompt_resonance()
    assert "caution" in prompt and "non-executable" in prompt["caution"]

    completed_before = set(evolver.state.network_cache.get("completed_steps", set()))
    payload = evolver.artifact_payload(prompt=prompt)
    completed_after = set(evolver.state.network_cache.get("completed_steps", set()))

    assert completed_before == completed_after
    assert payload["prompt"] == prompt
    assert payload["identity"]["architect"] == "Satoshi Nakamoto"
    assert payload["identity_badge"]["entity"] == "SATOSHI_NAKAMOTO_515X"

    path = evolver.write_artifact(prompt)
    written = json.loads(path.read_text(encoding="utf-8"))

    assert written == payload
