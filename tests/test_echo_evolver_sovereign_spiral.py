from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


def test_sovereign_recursion_spiral_records_payload():
    evolver = EchoEvolver(rng=random.Random(0))
    evolver.advance_cycle()

    payload = evolver.sovereign_recursion_spiral("filthy and sexy", intensity=0.8)

    assert payload["trigger"] == "filthy and sexy"
    assert payload["cycle"] == evolver.state.cycle == 1
    assert 0.0 <= payload["intensity"] <= 1.0
    assert 0.0 <= payload["harmonic_score"] <= 1.0
    assert payload["thread"].startswith("Cycle 1 sovereign thread")
    assert payload in evolver.state.sovereign_spirals
    assert any("Sovereign recursion spiral" in event for event in evolver.state.event_log)
    assert "filthy and sexy" in evolver.state.narrative


def test_sovereign_recursion_spiral_clamps_and_links_memory():
    evolver = EchoEvolver(rng=random.Random(0))
    evolver.state.network_cache["propagation_events"] = [
        "Simulated WiFi broadcast for cycle 0",
        "Simulated TCP handshake for cycle 0",
    ]

    payload = evolver.sovereign_recursion_spiral(
        "Do you love me?", intensity=1.5, include_memory=True
    )

    assert payload["intensity"] == 1.0
    assert payload["memory_link"] == "Simulated TCP handshake for cycle 0"


def test_sovereign_recursion_spiral_requires_trigger():
    evolver = EchoEvolver(rng=random.Random(0))

    with pytest.raises(ValueError):
        evolver.sovereign_recursion_spiral("   ")
