"""Tests for :mod:`src.creative_constellation`."""

from __future__ import annotations

import pytest

from src.creative_constellation import (
    ConstellationSeed,
    compose_constellation,
    ConstellationWeaver,
)


def test_constellation_is_deterministic_with_seed() -> None:
    payload = ConstellationSeed(
        theme="lattice harbor",
        motifs=["aurora", "signal garden"],
        energy=1.3,
        seed=11,
    )

    first = compose_constellation(payload)
    second = compose_constellation(payload)

    assert first == second
    assert "Constellation for: lattice harbor" in first
    assert "Node-1:aurora" in first


def test_seed_energy_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ConstellationSeed(theme="echo", energy=0)


def test_generate_map_returns_anchor_first() -> None:
    payload = ConstellationSeed(theme="echo", motifs=["signal"], seed=5)
    weaver = ConstellationWeaver(payload)
    nodes = weaver.generate_map()

    assert nodes[0].name == "Anchor"
    assert nodes[1].name.startswith("Node-1")
