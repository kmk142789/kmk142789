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

    timeline = evolver.state.network_cache["propagation_ledger"]
    assert len(timeline) == 1
    ledger_entry = timeline[0]
    assert ledger_entry["version"] == 1
    assert ledger_entry["cycle"] == 0
    assert ledger_entry["mode"] == "simulated"
    assert ledger_entry["events"] == events
    assert ledger_entry["summary"] == evolver.state.network_cache["propagation_summary"]
    assert isinstance(ledger_entry["timestamp_ns"], int)
    assert ledger_entry["timestamp_iso"].endswith("+00:00")
    assert ledger_entry["previous_hash"] == "0" * 64
    assert len(ledger_entry["hash"]) == 64
    assert (
        evolver.state.network_cache["propagation_timeline_hash"]
        == ledger_entry["hash"]
    )


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

    live_timeline = cache["propagation_ledger"]
    assert len(live_timeline) == 1
    live_entry = live_timeline[0]
    assert live_entry["version"] == 1
    assert live_entry["cycle"] == 3
    assert live_entry["mode"] == "live"
    assert live_entry["events"] == events
    assert live_entry["summary"] == cache["propagation_summary"]
    assert live_entry["previous_hash"] == "0" * 64
    assert len(live_entry["hash"]) == 64
    assert cache["propagation_timeline_hash"] == live_entry["hash"]
