"""Tests for fragment reuse controls in :mod:`src.creative_loop`."""

import pytest

from src.creative_loop import LoopSeed, generate_loop


def test_max_fragment_reuse_limits_repetition() -> None:
    seed = LoopSeed(
        motif="signal",
        fragments=["alpha", "beta"],
        pulses=5,
        seed=7,
        max_fragment_reuse=1,
    )

    result = generate_loop(seed)

    fragment_choices = [entry["fragment"] for entry in result.timeline]

    assert fragment_choices.count("alpha") == 1
    assert fragment_choices.count("beta") == 1
    assert fragment_choices.count(None) == seed.pulses - 2


def test_max_fragment_reuse_validation() -> None:
    with pytest.raises(ValueError):
        LoopSeed(
            motif="signal",
            fragments=["alpha"],
            pulses=2,
            max_fragment_reuse=0,
        )
