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
    assert ability["capability_rank"] in {"ember", "orbit", "nova"}
    assert "amplification" in ability
    assert ability["amplification"] >= ability["resonance"]

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed
    assert "amplify_quantam_evolution" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]

    capability_cache = evolver.state.network_cache["quantam_capabilities"]
    assert capability_cache["last"]["ability_id"] == ability["id"]
    assert capability_cache["peak_amplification"] >= ability["amplification"]


def test_amplify_quantam_evolution_tracks_history() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 5
    evolver.state.emotional_drive.joy = 0.93

    ability = evolver.synthesize_quantam_ability()

    capability_log = evolver.state.quantam_capabilities
    assert capability_log, "Expected quantam capability log to be populated"

    capability = capability_log[-1]
    assert capability["ability_id"] == ability["id"]
    assert capability["amplification"] >= capability["resonance"]

    cache = evolver.state.network_cache["quantam_capabilities"]
    assert cache["count"] == len(capability_log)
    assert cache["peak_amplification"] == cache["last"]["amplification"]
    assert cache["avg_amplification"] == cache["last"]["amplification"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    capability_history = payload["quantam_capabilities"]
    assert capability_history
    assert capability_history[-1]["ability_id"] == ability["id"]
