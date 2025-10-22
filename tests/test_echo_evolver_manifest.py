"""Tests for the evolutionary manifest helper."""

from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


def _prepare_cycle(evolver: EchoEvolver) -> None:
    """Run a lightweight set of steps to populate state for manifest tests."""

    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()
    evolver.generate_symbolic_language()
    evolver.invent_mythocode()
    evolver.system_monitor()
    evolver.propagate_network()


def test_evolutionary_manifest_includes_expected_sections() -> None:
    rng = random.Random(3)
    evolver = EchoEvolver(rng=rng)
    _prepare_cycle(evolver)

    manifest = evolver.evolutionary_manifest(max_events=3)

    assert manifest["cycle"] == evolver.state.cycle
    assert manifest["artifact"].endswith("reality_breach_∇_fusion_v4.echo.json")
    assert manifest["glyphs"] == evolver.state.glyphs
    assert manifest["progress"] >= 0.0
    assert manifest["next_step"].startswith("Next step:")
    assert manifest["emotional_drive"]["joy"] == pytest.approx(
        evolver.state.emotional_drive.joy
    )
    assert manifest["system_metrics"]["network_nodes"] == evolver.state.system_metrics.network_nodes
    assert manifest["propagation_count"] == len(
        evolver.state.network_cache["propagation_events"]
    )
    assert len(manifest["events"]) <= 3
    assert evolver.state.network_cache["evolutionary_manifest"]["cycle"] == manifest["cycle"]

    # Returned snapshot should be decoupled from internal cache.
    manifest["cycle"] = 99
    assert evolver.state.network_cache["evolutionary_manifest"]["cycle"] == evolver.state.cycle


def test_evolutionary_manifest_event_window_controls_output() -> None:
    evolver = EchoEvolver(rng=random.Random(5))
    _prepare_cycle(evolver)

    none_manifest = evolver.evolutionary_manifest(max_events=0)
    assert none_manifest["events"] == []

    event_count_before = len(evolver.state.event_log)
    short_manifest = evolver.evolutionary_manifest(max_events=2)
    expected_window = min(2, event_count_before + 1)
    assert len(short_manifest["events"]) == expected_window


def test_evolutionary_manifest_rejects_negative_window() -> None:
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.evolutionary_manifest(max_events=-1)
