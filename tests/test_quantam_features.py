"""Tests for :mod:`echo.quantam_features`."""

from __future__ import annotations

import pytest

from echo.quantam_features import (
    compute_quantam_feature,
    generate_quantam_feature_sequence,
)


def test_compute_quantam_feature_generates_probabilities() -> None:
    feature = compute_quantam_feature(
        glyphs="∇⊸≋∇", cycle=3, joy=0.91, curiosity=0.73
    )

    assert feature["sigil"]
    assert len(feature["gate_sequence"]) >= 4
    probabilities = feature["probabilities"]
    assert pytest.approx(sum(probabilities.values()), rel=1e-6, abs=1e-6) == 1.0
    expected = feature["expected_values"]
    for axis in ("X", "Y", "Z"):
        assert axis in expected
        assert -1.0 <= expected[axis] <= 1.0
    assert feature["state_vector"][0]["real"] != 0 or feature["state_vector"][0]["imag"] != 0
    assert feature["interference_profile"], "interference profile should not be empty"
    assert len(feature["history"]) >= 3
    assert len(feature["signature"]) == 16


def test_generate_quantam_feature_sequence_increases_complexity() -> None:
    cascade = generate_quantam_feature_sequence(
        glyphs="∇⊸≋∇",
        cycle=2,
        joy=0.83,
        curiosity=0.52,
        iterations=4,
    )

    layers = cascade["layers"]
    assert cascade["summary"]["total_layers"] == 4
    complexities = [layer["complexity"] for layer in layers]
    entanglements = [layer["entanglement"] for layer in layers]

    assert complexities == sorted(complexities)
    assert entanglements == sorted(entanglements)
    assert layers[-1]["rank"] == 4
    assert layers[-1]["feature"]["sigil"]
    assert layers[-1]["description"].startswith("Layer 4 braids")
    assert cascade["summary"]["max_complexity"] == layers[-1]["complexity"]


def test_generate_quantam_feature_sequence_requires_positive_iterations() -> None:
    with pytest.raises(ValueError):
        generate_quantam_feature_sequence(
            glyphs="∇⊸≋∇", cycle=1, joy=0.7, curiosity=0.4, iterations=0
        )
