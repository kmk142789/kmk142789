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

