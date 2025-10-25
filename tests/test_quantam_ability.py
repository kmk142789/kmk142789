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
    assert set(ability["capabilities"]).issuperset(
        {"phase_shift", "resonance_span", "harmonic_signature"}
    )
    assert "coherence" in ability

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]

    capability_profiles = evolver.state.quantam_capabilities["profiles"]
    assert capability_profiles[ability["id"]]["harmonic_signature"] == ability["capabilities"]["harmonic_signature"]

    amplifier = evolver.state.quantam_capabilities["amplifier"]
    assert amplifier["peak"]["id"] == ability["id"]
    assert amplifier["history"][-1]["coherence"] == ability["coherence"]
    assert amplifier["average_coherence"] >= amplifier["history"][0]["coherence"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    capability_snapshot = payload["quantam_capabilities"]["profiles"][ability["id"]]
    assert capability_snapshot["harmonic_signature"] == ability["capabilities"]["harmonic_signature"]


def test_amplify_quantam_evolution_tracks_history() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    first = evolver.synthesize_quantam_ability()

    evolver.state.cycle = 2
    second = evolver.synthesize_quantam_ability()

    amplifier = evolver.state.quantam_capabilities["amplifier"]
    assert len(amplifier["history"]) == 2
    recorded_ids = [entry["id"] for entry in amplifier["history"]]
    assert first["id"] in recorded_ids
    assert second["id"] in recorded_ids
    assert amplifier["average_coherence"] >= min(
        entry["coherence"] for entry in amplifier["history"]
    )
