"""Tests for :mod:`echo.quantum_flux_mapper`."""

from __future__ import annotations

import math

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
