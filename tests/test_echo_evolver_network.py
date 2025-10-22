"""Tests covering the evolver's network propagation simulation."""

from __future__ import annotations

import random

from echo.evolver import EchoEvolver


def test_propagate_network_simulated_records_cache_and_log() -> None:
    evolver = EchoEvolver(rng=random.Random(1))

    events = evolver.propagate_network(enable_network=False)

    assert len(events) == 5
    assert events[:4] == [
        "Simulated WiFi broadcast for cycle 0",
        "Simulated TCP handshake for cycle 0",
        "Bluetooth glyph packet staged for cycle 0",
        "IoT trigger drafted with key N/A",
    ]

    metrics = evolver.state.system_metrics
    assert events[-1] == f"Orbital hop simulation recorded ({metrics.orbital_hops} links)"

    # The simulated events are cached for downstream tooling and marked as complete.
    assert evolver.state.network_cache["propagation_events"] == events
    assert evolver.state.network_cache["propagation_mode"] == "simulated"
    assert evolver.state.network_cache["propagation_summary"].startswith(
        "Network propagation (simulated) captured across 5 channels"
    )
    completed = evolver.state.network_cache["completed_steps"]
    assert "propagate_network" in completed

    # The summary log makes it easy for higher level routines to introspect behaviour.
    assert evolver.state.event_log[-1].startswith("Network propagation (simulated) captured across 5 channels")


def test_propagate_network_live_reports_live_channels() -> None:
    rng = random.Random(7)
    evolver = EchoEvolver(rng=rng)
    evolver.state.cycle = 3

    events = evolver.propagate_network(enable_network=True)

    assert events == [
        "WiFi channel engaged for cycle 3",
        "TCP channel engaged for cycle 3",
        "Bluetooth channel engaged for cycle 3",
        "IoT channel engaged for cycle 3",
        "Orbital channel engaged for cycle 3",
    ]

    cache = evolver.state.network_cache
    assert cache["propagation_mode"] == "live"
    assert cache["propagation_summary"].startswith(
        "Network propagation (live) captured across 5 channels"
    )
    log_entry = evolver.state.event_log[-1]
    assert "Network propagation (live) captured across 5 channels" in log_entry
