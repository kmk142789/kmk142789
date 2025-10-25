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
    assert ability["capabilities"]
    assert ability["capability_score"] == round(
        sum(cap["charge"] for cap in ability["capabilities"]), 3
    )
    assert ability["evolution_gain"] >= ability["entanglement"]

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed
    assert "amplify_quantam_evolution" in completed

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
    profile = payload["quantam_capability_index"]
    assert profile["cycles_observed"] == 1
    assert ability["capabilities"][0]["name"] in profile["capability_counts"]


def test_amplify_quantam_evolution_accumulates_profile() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 3
    ability_one = evolver.synthesize_quantam_ability()
    evolver.state.cycle = 4
    ability_two = evolver.synthesize_quantam_ability()

    profile = evolver.state.quantam_capability_index

    assert profile["cycles_observed"] == 2
    assert profile["total_entanglement"] == round(
        ability_one["entanglement"] + ability_two["entanglement"], 3
    )
    assert profile["joy_charge_peak"] >= max(
        ability_one["joy_charge"], ability_two["joy_charge"]
    )
    for ability in (ability_one, ability_two):
        for capability in ability["capabilities"]:
            assert profile["capability_counts"][capability["name"]] >= 1

    cached_profile = evolver.state.network_cache["quantam_evolution_profile"]
    assert cached_profile["cycles_observed"] == 2
