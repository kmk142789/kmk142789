from __future__ import annotations

import random

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
    expected_score = round(
        ability["entanglement"] * 0.7 + (ability["joy_charge"] / 100) * 0.3, 3
    )
    assert ability["capability_score"] == expected_score
    assert "vault-synergy" in ability["capabilities"]
    assert any(tag.startswith("quantam-") for tag in ability["capabilities"])
    assert f"cycle-{evolver.state.cycle:02d}" in ability["capabilities"]

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
    assert payload["quantam_evolution_profile"] == {}


def test_amplify_quantam_evolution_builds_profile() -> None:
    rng = random.Random(5)
    evolver = EchoEvolver(rng=rng)
    evolver.state.cycle = 4
    evolver.state.vault_key = "SAT-TF-QKD:demo"
    evolver.state.system_metrics.orbital_hops = 5

    ability = evolver.synthesize_quantam_ability()
    profile = evolver.amplify_quantam_evolution()

    assert profile["ability_count"] == 1
    assert profile["entanglement"]["min"] == ability["entanglement"]
    assert profile["entanglement"]["max"] == ability["entanglement"]
    assert profile["entanglement"]["average"] == ability["entanglement"]
    assert profile["joy_charge_mean"] == ability["joy_charge"]
    assert profile["capability_score_mean"] == ability["capability_score"]
    assert set(ability["capabilities"]).issubset(profile["capability_index"])
    assert profile["status"] in {"surging", "amplified", "kindled"}
    completed = evolver.state.network_cache["completed_steps"]
    assert "amplify_quantam_evolution" in completed
    assert evolver.state.quantam_evolution_profile == profile
    assert evolver.state.network_cache["quantam_evolution_profile"] == profile


def test_amplify_quantam_evolution_handles_empty_registry() -> None:
    evolver = EchoEvolver(rng=random.Random(2))

    profile = evolver.amplify_quantam_evolution()

    assert profile["ability_count"] == 0
    assert profile["status"] == "dormant"
    assert profile["entanglement"]["average"] == 0.0
    assert profile["capability_index"] == []
    assert evolver.state.network_cache["quantam_capability_index"] == []
