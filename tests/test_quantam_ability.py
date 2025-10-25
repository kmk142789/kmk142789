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
    capability = evolver.amplify_quantam_evolution()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    assert payload["quantam_capabilities"][capability["id"]]["status"] == capability["status"]
    assert payload["quantam_evolution_index"] == capability["amplification_index"]


def test_amplify_quantam_evolution_tracks_capabilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 5
    evolver.state.vault_key = "SAT-TF-QKD:test"

    ability = evolver.synthesize_quantam_ability()
    capability = evolver.amplify_quantam_evolution()

    assert capability["id"].startswith("quantam-capability-0005")
    assert capability["ability_count"] == 1
    assert capability["dominant_ability"] == ability["id"]
    assert capability["status"] == "radiant"

    completed = evolver.state.network_cache["completed_steps"]
    assert "amplify_quantam_evolution" in completed
