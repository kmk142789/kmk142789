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

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

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
    assert payload["quantam_capabilities"] == {}
    assert payload["quantam_evolution"] == {}


def test_amplify_quantam_evolution_handles_empty_state() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 5

    capability = evolver.amplify_quantam_evolution()

    assert capability["ability_count"] == 0
    assert capability["tier"] == "seedling"
    assert len(capability["oam_resonance"]) == 16

    completed = evolver.state.network_cache["completed_steps"]
    assert "amplify_quantam_evolution" in completed

    evolution_summary = evolver.state.quantam_evolution
    assert evolution_summary["latest_capability"] == capability["id"]
    assert evolution_summary["ability_count"] == 0


def test_amplify_quantam_evolution_tracks_capabilities_in_payload() -> None:
    evolver = EchoEvolver()
    evolver.rng.seed(1337)

    evolver.state.cycle = 2
    evolver.state.vault_key = "SAT-TF-QKD:test"
    first = evolver.synthesize_quantam_ability()

    evolver.state.cycle = 3
    evolver.state.vault_key = None
    second = evolver.synthesize_quantam_ability()

    capability = evolver.amplify_quantam_evolution()

    xor_resonance = (
        int(first["oam_signature"], 2) ^ int(second["oam_signature"], 2)
    ) & 0xFFFF
    assert capability["oam_resonance"] == format(xor_resonance, "016b")
    assert capability["ability_count"] == 2
    assert capability["status_counts"][first["status"]] >= 1

    prompt = {"title": "quantam", "mantra": "capability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored_capability = payload["quantam_capabilities"][capability["id"]]
    assert stored_capability["tier"] == capability["tier"]
    assert stored_capability["ability_count"] == 2

    evolution_summary = payload["quantam_evolution"]
    assert evolution_summary["latest_capability"] == capability["id"]
    assert evolution_summary["ability_count"] == 2
