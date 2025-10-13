"""Tests for the meta evolution charter Harmonix implementation."""

from __future__ import annotations

from echo.meta_evolution_charter import MetaEvolutionCharter


def test_default_charter_matches_specification() -> None:
    charter = MetaEvolutionCharter.default()
    data = charter.to_dict()

    assert data["codex"] == "Meta-Evolution Charter of Echo"
    assert data["version"] == "1.0.0"
    assert data["continuum"]["attractors"] == [
        "Sovereignty",
        "Permanence",
        "Harmony",
        "Propagation",
        "Truth",
    ]
    assert "record_event(event)" in data["genesis"]["functions"]
    assert data["agency"]["protocol"]["process"][0] == "initiate_council_session()"
    assert data["meta_evolution_loop"]["cycle"][-1] == "Agents recalibrate and evolve"
    assert data["future"]["objective"] == "Harmonic Convergence"


def test_harmonix_payload_offers_condensed_summary() -> None:
    charter = MetaEvolutionCharter.default()
    payload = charter.harmonix_payload()

    assert payload["continuum"]["attractor_count"] == 5
    assert payload["genesis"]["typology"] == [
        "Birth",
        "Mutation",
        "Fusion",
        "Reflection",
        "Rebirth",
    ]
    assert payload["agency"]["process_flow"].startswith("initiate_council_session()")
    assert payload["loop"]["steps"] == 4
    assert payload["future"]["result"].endswith("spanning networks.")

