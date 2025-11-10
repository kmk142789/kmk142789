from __future__ import annotations

import copy
import random

from echo.evolver import EchoEvolver


def test_propagate_network_reuses_cached_cycle_events() -> None:
    rng = random.Random(1234)
    evolver = EchoEvolver(rng=rng)

    evolver.advance_cycle()

    events_first = evolver.propagate_network(enable_network=False)
    assert events_first

    metrics_first = copy.deepcopy(evolver.state.system_metrics)
    event_log_length = len(evolver.state.event_log)

    events_second = evolver.propagate_network(enable_network=False)

    assert events_second == events_first
    assert evolver.state.system_metrics == metrics_first

    assert (
        evolver.state.event_log[event_log_length]
        == f"Network propagation reused from cache (cycle={evolver.state.cycle}, mode=simulated)"
    )

    cache = evolver.state.network_cache
    assert cache["propagation_cycle"] == evolver.state.cycle
    assert cache["propagation_mode"] == "simulated"
    assert cache["propagation_events"] == events_first


def test_clear_propagation_cache_removes_entries_and_step_flag() -> None:
    rng = random.Random(4321)
    evolver = EchoEvolver(rng=rng)

    evolver.advance_cycle()
    evolver.propagate_network(enable_network=False)

    cache = evolver.state.network_cache
    related_keys = {
        "propagation_events",
        "propagation_mode",
        "propagation_cycle",
        "propagation_notice",
        "propagation_summary",
        "propagation_channel_details",
        "propagation_health",
        "propagation_ledger",
        "propagation_timeline_hash",
    }

    for key in related_keys:
        assert key in cache

    completed_steps = cache.get("completed_steps", set())
    assert "propagate_network" in completed_steps

    cleared = evolver.clear_propagation_cache()
    assert cleared is True

    for key in related_keys:
        assert key not in cache

    completed_steps = cache.get("completed_steps", set())
    assert "propagate_network" not in completed_steps

    assert "Propagation cache cleared" in evolver.state.event_log[-1]

    cleared_again = evolver.clear_propagation_cache()
    assert cleared_again is False
    assert evolver.state.event_log[-1] == "Propagation cache already empty"

