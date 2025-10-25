from __future__ import annotations

from echo.evolver import EchoEvolver


def test_synthesize_quantam_ability_records_cache() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 2
    evolver.state.glyphs = "∇⊸≋∇"
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    ability = evolver.synthesize_quantam_ability()

    assert ability["id"] in evolver.state.quantam_abilities
    assert ability["status"] == "ignited"
    assert len(ability["oam_signature"]) == 16
    assert 0.72 <= ability["entanglement"] <= 0.96
    assert ability["capability_id"].endswith("-capability")
    assert ability["capability_potency"] == evolver.state.quantam_capabilities[ability["capability_id"]]["potency"]

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed
    assert "register_quantam_capability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    capability_id = stored["capability_id"]
    assert capability_id in payload["quantam_capabilities"]

    evolution = payload["quantam_evolution"]
    assert evolution["ability_count"] >= 1
    assert evolution["capability_count"] >= 1


def test_amplify_quantam_evolution_records_summary() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 3

    evolver.synthesize_quantam_ability()
    summary = evolver.amplify_quantam_evolution()

    assert summary["ability_count"] == len(evolver.state.quantam_abilities)
    assert summary["capability_count"] == len(evolver.state.quantam_capabilities)
    assert "quantam_evolution" in evolver.state.network_cache
    assert "amplify_quantam_evolution" in evolver.state.network_cache["completed_steps"]
