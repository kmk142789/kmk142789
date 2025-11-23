"""Tests for the holographic resonance manifold feature."""

import random

from packages.core.src.echo.evolver import (
    EchoEvolver,
    HolographicResonanceBand,
    HolographicResonanceMap,
    _GLYPH_RING,
)


def test_holographic_resonance_topology_is_deterministic():
    evolver = EchoEvolver(rng=random.Random(0), time_source=lambda: 123456789)

    manifold = evolver.holographic_resonance_topology(
        layers=2, threads_per_layer=2, momentum_window=2
    )

    assert isinstance(manifold, HolographicResonanceMap)
    assert manifold.world_first_stamp == "f4f63167b33b29d2f2cb57be52bbf9e7"
    assert manifold.coherence == 0.4743
    assert manifold.flux_gradient == 1.0
    assert manifold.novelty == 0.1656
    assert manifold.stability == 0.332
    assert manifold.trend == "no signal"
    assert manifold.confidence == "low"

    assert len(manifold.bands) == 4
    assert all(isinstance(band, HolographicResonanceBand) for band in manifold.bands)
    assert manifold.bands[0].glyph == _GLYPH_RING[0]
    assert manifold.bands[-1].glyph == _GLYPH_RING[1]
    assert manifold.bands[0].amplitude == 0.5346
    assert manifold.bands[-1].phase_offset == 0.25


def test_holographic_resonance_description_uses_cache():
    evolver = EchoEvolver(rng=random.Random(0), time_source=lambda: 123456789)

    # Seed the map once and ensure describe reuses cached payload
    first_map = evolver.holographic_resonance_topology(
        layers=2, threads_per_layer=2, momentum_window=2
    ).as_dict()
    report = evolver.describe_holographic_resonance()

    assert "Holographic resonance map" in report
    assert "coherence 0.474" in report
    assert evolver.state.network_cache["holographic_resonance"] == first_map
    assert "Layer 01 Thread 01" in report
    assert "…" not in report
