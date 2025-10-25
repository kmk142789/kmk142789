from __future__ import annotations

import random

from echo.evolver import EchoEvolver


def test_synthesize_quantam_ability_records_cache() -> None:
    evolver = EchoEvolver(rng=random.Random(7))
    evolver.state.cycle = 2
    evolver.state.glyphs = "∇⊸≋∇"
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    ability = evolver.synthesize_quantam_ability()

    assert ability["id"] in evolver.state.quantam_abilities
    assert ability["status"] == "ignited"
    assert len(ability["oam_signature"]) == 16
    assert 0.72 <= ability["entanglement"] <= 0.96
    assert "capabilities" in ability
    capability = ability["capabilities"]
    assert capability["resonance_band"] in {"stellar", "luminous", "ember"}
    assert ability["id"] in evolver.state.quantam_capabilities
    cached_capability = evolver.state.network_cache["quantam_capabilities"][ability["id"]]
    assert cached_capability["resonance_band"] == capability["resonance_band"]

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver(rng=random.Random(3))
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    assert payload["quantam_capabilities"][ability["id"]]["coherence"] == ability["capabilities"]["coherence"]
    assert payload["quantam_evolution"] == {}


def test_amplify_quantam_evolution_summary() -> None:
    rng = random.Random(5)
    evolver = EchoEvolver(rng=rng)
    evolver.state.cycle = 3
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    ability = evolver.synthesize_quantam_ability()
    summary = evolver.amplify_quantam_evolution()

    assert summary["ability_count"] == 1
    assert summary["dominant_band"] == ability["capabilities"]["resonance_band"]
    assert summary["status"] in {"forming", "ignited", "ascendant"}
    assert evolver.state.quantam_evolution == summary
    assert (
        evolver.state.network_cache["quantam_evolution_summary"]["ability_count"]
        == summary["ability_count"]
    )
    completed = evolver.state.network_cache["completed_steps"]
    assert "amplify_quantam_evolution" in completed
