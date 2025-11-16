"""Tests for :mod:`echo.quantum_features`."""

from __future__ import annotations

import math

import pytest

from echo.quantum_features import QuantumFeature, generate_quantum_features


def test_generate_quantum_features_increases_with_levels() -> None:
    features_level_1 = generate_quantum_features([1 + 0j, 0.3 + 0.4j], levels=1)
    features_level_3 = generate_quantum_features([1 + 0j, 0.3 + 0.4j], levels=3)

    assert len(features_level_1) == 3
    assert len(features_level_3) == 9
    assert all(feature.complexity == 1 for feature in features_level_1)
    assert features_level_3[0].name == "probability_mass"
    assert math.isclose(features_level_3[0].value, 1.0, rel_tol=1e-9)


def test_generate_quantum_features_accepts_higher_orders() -> None:
    features = generate_quantum_features([1 + 0j, 1j, 0.5 + 0.25j], levels=5)
    names = [feature.name for feature in features]
    assert "probability_moment_4" in names
    assert "probability_moment_5" in names
    assert names.index("probability_moment_4") < names.index("probability_moment_5")
    assert features[-1].complexity == 5


def test_generate_quantum_features_validates_state() -> None:
    with pytest.raises(ValueError):
        generate_quantum_features([], levels=1)

    with pytest.raises(ValueError):
        generate_quantum_features([0 + 0j, 0 + 0j], levels=2)


def test_quantum_feature_dataclass_round_trip() -> None:
    feature = QuantumFeature(name="test", complexity=2, value=0.42)
    assert feature.name == "test"
    assert feature.complexity == 2
    assert feature.value == 0.42
