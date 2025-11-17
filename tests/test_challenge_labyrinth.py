"""Tests for the :mod:`echo.challenge_labyrinth` module."""

from __future__ import annotations

from types import SimpleNamespace

import asyncio
import pytest

from echo.challenge_labyrinth import ChallengeLabyrinth, design_extreme_challenge


@pytest.fixture()
def sample_blueprint() -> dict:
    return {
        "entrypoint": "alpha",
        "seed": 7,
        "emphasis_tags": ["mythic", "fractal"],
        "layers": [
            {
                "name": "alpha",
                "vectors": [
                    {"axis": "myth", "magnitude": 5.0, "volatility": 0.8, "tags": ["mythic"]},
                    {"axis": "logic", "magnitude": 2.5, "volatility": 0.2},
                ],
                "edges": ["beta", "gamma"],
                "resonance": 1.1,
                "depth": 0,
            },
            {
                "name": "beta",
                "vectors": [
                    {"axis": "myth", "magnitude": 3.0, "volatility": 0.3, "tags": ["fractal"]},
                    {"axis": "systems", "magnitude": 4.2, "volatility": 0.1},
                ],
                "edges": ["delta"],
                "resonance": 0.9,
                "depth": 1,
            },
            {
                "name": "gamma",
                "vectors": [
                    {"axis": "curiosity", "magnitude": 1.7, "volatility": 0.6},
                ],
                "edges": [],
                "resonance": 1.4,
                "depth": 1,
            },
            {
                "name": "delta",
                "vectors": [
                    {"axis": "logic", "magnitude": 2.1, "volatility": 0.4},
                    {"axis": "systems", "magnitude": 1.0, "volatility": 0.1},
                ],
                "edges": [],
                "resonance": 1.6,
                "depth": 2,
            },
        ],
    }


def test_labyrinth_traversal_emits_consistent_report(sample_blueprint: dict) -> None:
    labyrinth = ChallengeLabyrinth.from_blueprint(sample_blueprint, seed=sample_blueprint["seed"])
    report = asyncio.run(labyrinth.traverse(iterations=3, concurrency=2))
    assert report.total_intensity > 0
    assert set(report.layers_visited).issubset({"alpha", "beta", "gamma", "delta"})
    assert 0.0 <= report.completion_ratio <= 1.0
    assert {"myth", "logic", "curiosity", "systems"}.issuperset(report.synthesis.keys())


def test_design_extreme_challenge_honors_evolver_cycle(sample_blueprint: dict) -> None:
    baseline = design_extreme_challenge(sample_blueprint, iterations=2, concurrency=2)
    evolver = SimpleNamespace(state=SimpleNamespace(cycle=50))
    boosted = design_extreme_challenge(
        sample_blueprint,
        evolver=evolver,  # type: ignore[arg-type] - only needs cycle attribute
        iterations=2,
        concurrency=2,
    )
    assert boosted.total_intensity > baseline.total_intensity
