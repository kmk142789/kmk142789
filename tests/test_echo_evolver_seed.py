import random

import pytest

from echo.evolver import EchoEvolver


def test_seed_initialises_deterministic_rng() -> None:
    first = EchoEvolver(seed=7)
    second = EchoEvolver(seed=7)

    assert first.emotional_modulation() == second.emotional_modulation()


def test_seed_with_rng_conflict_raises() -> None:
    with pytest.raises(ValueError):
        EchoEvolver(seed=3, rng=random.Random(9))
