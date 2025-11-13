"""Tests for :mod:`echo.quantam_features`."""

from __future__ import annotations

import pytest

from echo.quantam_features import compute_quantam_feature


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
