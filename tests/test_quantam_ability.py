from __future__ import annotations

import random

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


def test_quantam_capability_matrix_tracks_metrics() -> None:
    evolver = EchoEvolver(rng=random.Random(7))
    evolver.state.cycle = 3
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    abilities = []
    for cycle in range(1, 4):
        evolver.state.cycle = cycle
        abilities.append(evolver.synthesize_quantam_ability())

    matrix = evolver.quantam_capability_matrix()

    assert matrix["count"] == 3
    assert matrix["latest"] == max(abilities, key=lambda a: a["timestamp_ns"])["id"]
    assert "ignited" in matrix["status_counts"]

    completed = evolver.state.network_cache["completed_steps"]
    assert "quantam_capability_matrix" in completed
    assert evolver.state.quantam_capabilities["count"] == 3


def test_amplify_quantam_evolution_merges_payload() -> None:
    evolver = EchoEvolver(rng=random.Random(11))
    evolver.state.cycle = 2
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    evolver.synthesize_quantam_ability()

    payload = evolver.amplify_quantam_evolution(
        resonance_factor=1.5,
        include_sequence=False,
        include_reflection=False,
        include_propagation=False,
    )

    assert payload["resonance_factor"] == 1.5
    assert payload["quantam_capabilities"]["count"] >= 1
    assert payload["amplified_capabilities"]["resonance_factor"] == 1.5
    assert "quantam_amplification" in evolver.state.network_cache
