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
    assert set(ability["capabilities"]) == {
        "resonance",
        "stability",
        "lattice_strength",
        "band",
    }
    assert ability["amplification_index"] >= 0

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]
    assert cached["capabilities"]["band"] == ability["capabilities"]["band"]


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    evolution = payload["quantam_evolution"]
    assert evolution["ability_count"] == 1
    assert ability["capabilities"]["band"] in evolution["band_distribution"]


def test_amplify_quantam_evolution_tracks_summary() -> None:
    evolver = EchoEvolver()
    evolver.rng.seed(1234)

    evolver.state.cycle = 3
    ability_one = evolver.synthesize_quantam_ability()

    evolver.state.cycle = 4
    evolver.state.vault_key = "SAT-TF-QKD:demo"
    ability_two = evolver.synthesize_quantam_ability()

    summary = evolver.amplify_quantam_evolution()

    assert summary["ability_count"] == 2
    assert summary["latest_ability"] == ability_two["id"]
    assert summary["band_distribution"][ability_one["capabilities"]["band"]] >= 1
    expected_resonance = round(
        (
            ability_one["capabilities"]["resonance"]
            + ability_two["capabilities"]["resonance"]
        )
        / 2,
        3,
    )
    assert summary["mean_resonance"] == pytest.approx(expected_resonance)
    assert summary["amplification_peak"]["ability"] in {
        ability_one["id"],
        ability_two["id"],
    }
    assert evolver.state.quantam_evolution == summary
    assert evolver.state.network_cache["quantam_evolution"] == summary

    completed = evolver.state.network_cache["completed_steps"]
    assert "amplify_quantam_evolution" in completed
