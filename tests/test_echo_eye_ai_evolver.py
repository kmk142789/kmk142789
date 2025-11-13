"""Unit tests for the lightweight ``echo_eye_ai.evolver`` module."""

from __future__ import annotations

import pytest

from echo_eye_ai.evolver import EchoEvolver


def test_amplify_quantam_evolution_records_structured_capability() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 3
    evolver.state.vault_key = "SAT-TF-QKD:ready"

    ability = evolver.synthesize_quantam_ability()
    capability = evolver.amplify_quantam_evolution(ability)

    assert capability["ability"] == ability["id"]
    assert capability["status"] == "amplified"
    assert capability["id"] in evolver.state.quantam_capabilities
    stored = evolver.state.quantam_capabilities[capability["id"]]
    assert stored["resonance"] == capability["resonance"]
    assert stored["coherence"] == capability["coherence"]
    assert capability["feature_reference"] == ability["feature_signature"]
    assert capability["probability_zero"] + capability["probability_one"] == pytest.approx(1.0)


def test_synthesize_quantam_ability_updates_cache_and_status() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 6
    evolver.state.vault_key = "SAT-TF-QKD:active"

    ability = evolver.synthesize_quantam_ability()

    assert ability["status"] == "ignited"
    assert ability["joy_charge"] >= 90.0
    assert ability["timestamp_ns"] > 0

    cache = evolver.state.network_cache
    assert cache["last_quantam_ability"]["id"] == ability["id"]
    assert cache["last_quantam_feature"]["signature"] == ability["feature_signature"]
    assert ability["id"] in cache["quantam_abilities"]
    assert "synthesize_quantam_ability" in cache["completed_steps"]


def test_amplify_quantam_evolution_exposes_amplification_metrics() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 4
    evolver.state.vault_key = "SAT-TF-QKD:cache"

    ability = evolver.synthesize_quantam_ability()
    capability = evolver.amplify_quantam_evolution(ability)

    assert capability["status"] in {"amplified", "stabilizing"}
    assert capability["amplification"] >= 1.0
    assert capability["glyph_flux"] > 0.0
    assert 0.0 <= capability["stability"] <= 1.0
    assert capability["timestamp_ns"] >= ability["timestamp_ns"]

    cache = evolver.state.network_cache
    assert cache["last_quantam_capability"]["id"] == capability["id"]
    assert capability["id"] in cache["quantam_capabilities"]
    assert "amplify_quantam_evolution" in cache["completed_steps"]
