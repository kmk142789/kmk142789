from __future__ import annotations

import pytest

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
    feature = ability["feature"]
    assert feature["signature"] == ability["feature_signature"]
    assert pytest.approx(sum(feature["probabilities"].values()), rel=1e-6, abs=1e-6) == 1.0

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()
    capability = evolver.amplify_quantam_evolution(ability=ability)

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]

    amplified = payload["quantam_capabilities"][capability["id"]]
    assert amplified["ability"] == ability["id"]
    assert amplified["status"] == capability["status"]
    assert amplified["feature_reference"] == ability["feature_signature"]


def test_amplify_quantam_evolution_tracks_capability_cache() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 5
    evolver.state.glyphs = "∇⊸≋∇≋"
    evolver.state.vault_key = "SAT-TF-QKD:active"

    ability = evolver.synthesize_quantam_ability()
    capability = evolver.amplify_quantam_evolution(ability=ability)

    assert capability["id"] in evolver.state.quantam_capabilities
    assert capability["status"] == "amplified"
    assert capability["amplification"] >= 1.0
    assert capability["feature_reference"] == ability["feature_signature"]
    assert capability["probability_zero"] + capability["probability_one"] == pytest.approx(1.0)

    cache = evolver.state.network_cache
    assert cache["last_quantam_capability"]["id"] == capability["id"]
    assert "amplify_quantam_evolution" in cache["completed_steps"]
