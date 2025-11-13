"""Unit tests for the lightweight ``echo_eye_ai.evolver`` module."""

from __future__ import annotations

import pytest

from echo_eye_ai.evolver import EchoEvolver


def test_amplify_quantam_evolution_records_structured_capability() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 3

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
