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
    channel_details = evolver.state.network_cache["propagation_channel_details"]
    assert len(channel_details) == 5
    for detail, event in zip(channel_details, events):
        assert detail["message"] == event
        assert detail["mode"] == "simulated"
        assert 20.0 <= detail["latency_ms"] <= 120.0
        assert 0.82 <= detail["stability"] <= 0.995

    health = evolver.state.network_cache["propagation_health"]
    assert health["channel_count"] == 5
    assert health["mode"] == "simulated"
    assert 20.0 <= health["average_latency_ms"] <= 120.0
    assert 0.82 <= health["stability_floor"] <= 0.995
    completed = evolver.state.network_cache["completed_steps"]
    assert "propagate_network" in completed

    # The summary log makes it easy for higher level routines to introspect behaviour.
    assert any(
        entry.startswith("Network propagation (simulated) captured across 5 channels")
        for entry in evolver.state.event_log[-2:]
    )

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
    live_details = cache["propagation_channel_details"]
    assert [detail["channel"] for detail in live_details] == [
        "WiFi",
        "TCP",
        "Bluetooth",
        "IoT",
        "Orbital",
    ]
    assert {detail["mode"] for detail in live_details} == {"live"}
    live_health = cache["propagation_health"]
    assert live_health["mode"] == "live"
    assert live_health["channel_count"] == 5
    assert 20.0 <= live_health["average_latency_ms"] <= 120.0
    assert 0.82 <= live_health["stability_floor"] <= 0.995
    log_tail = evolver.state.event_log[-2:]
    assert any("Network propagation (live) captured across 5 channels" in entry for entry in log_tail)

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


def test_network_propagation_snapshot_returns_structured_view() -> None:
    rng = random.Random(2)
    evolver = EchoEvolver(rng=rng)

    expected_events = evolver.propagate_network(enable_network=False)
    snapshot = evolver.network_propagation_snapshot()

    assert snapshot.cycle == evolver.state.cycle
    assert snapshot.mode == "simulated"
    assert snapshot.events == expected_events
    assert snapshot.channels == len(expected_events)
    assert snapshot.network_nodes == evolver.state.system_metrics.network_nodes
    assert snapshot.orbital_hops == evolver.state.system_metrics.orbital_hops
    assert snapshot.summary == evolver.state.network_cache["propagation_summary"]
    assert (
        snapshot.timeline_hash
        == evolver.state.network_cache["propagation_timeline_hash"]
    )
    assert snapshot.timeline_length == len(
        evolver.state.network_cache["propagation_ledger"]
    )
    assert snapshot.timeline is None

    cache_snapshot = evolver.state.network_cache["propagation_snapshot"]
    assert cache_snapshot["mode"] == snapshot.mode
    assert cache_snapshot["channels"] == snapshot.channels
    assert cache_snapshot["timeline"] is None

    log_entry = evolver.state.event_log[-1]
    assert log_entry.startswith("Propagation snapshot exported")


def test_network_propagation_snapshot_handles_empty_state() -> None:
    evolver = EchoEvolver(rng=random.Random(3))

    snapshot = evolver.network_propagation_snapshot(include_timeline=True)

    assert snapshot.cycle == 0
    assert snapshot.mode == "none"
    assert snapshot.events == []
    assert snapshot.channels == 0
    assert snapshot.network_nodes == 0
    assert snapshot.orbital_hops == 0
    assert snapshot.summary == "No propagation events recorded yet."
    assert snapshot.timeline_hash is None
    assert snapshot.timeline_length == 0
    assert snapshot.timeline is None

    cache_snapshot = evolver.state.network_cache["propagation_snapshot"]
    assert cache_snapshot["mode"] == "none"
    assert cache_snapshot["channels"] == 0
    assert cache_snapshot["timeline"] is None
