from __future__ import annotations

import random

import pytest

from echo.evolver import EchoEvolver


def test_cycle_highlight_reel_includes_quantam_and_events() -> None:
    evolver = EchoEvolver(rng=random.Random(0))
    evolver.state.quantam_abilities = {"ability-1": {"descriptor": "glow"}}
    evolver.state.quantam_capabilities = {"cap-1": {"descriptor": "flare"}}

    reel = evolver.cycle_highlight_reel(
        event_limit=2, quantam_limit=1, momentum_samples=1
    )

    assert reel["cycle"] == 0
    assert reel["quantam_abilities"][0]["id"] == "ability-1"
    assert reel["quantam_capabilities"][0]["id"] == "cap-1"
    assert len(reel["recent_events"]) == 2
    assert "Cycle 0 highlight" in reel["summary"]

    assert evolver.state.network_cache["cycle_highlight_reel"] == reel
    assert "Cycle highlight reel composed" in evolver.state.event_log[-1]


def test_cycle_highlight_reel_validates_limits() -> None:
    evolver = EchoEvolver(rng=random.Random(0))

    with pytest.raises(ValueError):
        evolver.cycle_highlight_reel(event_limit=-1)
    with pytest.raises(ValueError):
        evolver.cycle_highlight_reel(quantam_limit=0)
    with pytest.raises(ValueError):
        evolver.cycle_highlight_reel(momentum_samples=0)
