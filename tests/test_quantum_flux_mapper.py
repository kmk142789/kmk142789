"""Tests for :mod:`echo.quantum_flux_mapper`."""

from __future__ import annotations

import math
import random

import pytest

from echo.quantum_flux_mapper import QuantumFluxMapper, STANDARD_GATES


def test_apply_gate_sequence_matches_expected_state():
    mapper = QuantumFluxMapper()
    mapper.apply_sequence(["H", "Z", "H"])
    assert mapper.state == (0 + 0j, 1 + 0j)
    assert mapper.history[-3:] == ["Applied H gate", "Applied Z gate", "Applied H gate"]


def test_bloch_coordinates_after_hadamard():
    mapper = QuantumFluxMapper()
    mapper.apply_gate("H")
    x, y, z = mapper.bloch_coordinates()
    assert math.isclose(x, 1.0, rel_tol=1e-9)
    assert math.isclose(y, 0.0, abs_tol=1e-9)
    assert math.isclose(z, 0.0, abs_tol=1e-9)


def test_expected_value_matches_z_projection():
    mapper = QuantumFluxMapper()
    mapper.apply_gate("X")
    assert mapper.expected_value("Z") == -1.0
    mapper.apply_gate("X")
    assert mapper.expected_value("Z") == 1.0


def test_interference_landscape_maps_probability_curve():
    mapper = QuantumFluxMapper()
    mapper.apply_gate("H")
    samples = mapper.interference_landscape(samples=8)
    assert len(samples) == 8
    # first sample corresponds to zero rotation, matching the base probability
    first_angle, first_probability = samples[0]
    assert math.isclose(first_angle, 0.0, abs_tol=1e-9)
    assert math.isclose(first_probability, 0.5, rel_tol=1e-9)


def test_measure_collapses_state():
    mapper = QuantumFluxMapper(state=(0 + 0j, 1 + 0j))
    outcome = mapper.measure()
    assert outcome == "1"
    assert mapper.state == (0 + 0j, 1 + 0j)
    assert "Measured |1⟩" in mapper.history[-1]


def test_standard_gates_catalog_contains_expected_entries():
    assert set(["H", "X", "Z"]).issubset(STANDARD_GATES)


def test_apply_rotation_balances_superposition():
    mapper = QuantumFluxMapper()
    mapper.apply_rotation("y", math.pi / 2)
    alpha, beta = mapper.state
    assert math.isclose(abs(alpha) ** 2, 0.5, rel_tol=1e-9)
    assert math.isclose(abs(beta) ** 2, 0.5, rel_tol=1e-9)
    assert mapper.history[-1].startswith("Applied RY rotation")


def test_apply_rotation_rejects_invalid_axis():
    mapper = QuantumFluxMapper()
    with pytest.raises(ValueError):
        mapper.apply_rotation("q", math.pi / 3)


def test_apply_noise_channel_bit_flip_triggers_with_probability_one():
    mapper = QuantumFluxMapper()
    mapper.apply_noise_channel("bit_flip", 1.0, rng=random.Random(0))
    assert mapper.state == (0 + 0j, 1 + 0j)
    assert "bit flip noise" in mapper.history[-1]


def test_apply_noise_channel_validates_probability_bounds():
    mapper = QuantumFluxMapper()
    with pytest.raises(ValueError):
        mapper.apply_noise_channel("bit_flip", 1.5)


def test_fidelity_with_returns_overlap_probability():
    mapper = QuantumFluxMapper()
    mapper.apply_gate("H")
    fidelity_same = mapper.fidelity_with(mapper.state)
    assert math.isclose(fidelity_same, 1.0, rel_tol=1e-9)

    fidelity_zero = mapper.fidelity_with((1 + 0j, 0 + 0j))
    assert math.isclose(fidelity_zero, 0.5, rel_tol=1e-9)
    assert mapper.history[-1].startswith("Computed fidelity")
