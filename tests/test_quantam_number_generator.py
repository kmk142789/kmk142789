from __future__ import annotations

import pytest

from echo.quantam_features import generate_quantam_numbers


def test_generate_quantam_numbers_is_deterministic() -> None:
    first = generate_quantam_numbers(glyphs="∇⊸≋∇", cycle=7, count=5, low=0.0, high=1.0)
    second = generate_quantam_numbers(glyphs="∇⊸≋∇", cycle=7, count=5, low=0.0, high=1.0)

    assert first == second
    assert len(first) == 5
    assert all(0.0 <= value <= 1.0 for value in first)


def test_generate_quantam_numbers_supports_custom_bounds() -> None:
    values = generate_quantam_numbers(glyphs="∇⊸≋∇", cycle=3, count=4, low=-5.0, high=5.0)

    assert len(values) == 4
    assert all(-5.0 <= value <= 5.0 for value in values)
    assert any(value < 0 for value in values)
    assert any(value > 0 for value in values)


def test_generate_quantam_numbers_requires_positive_count() -> None:
    with pytest.raises(ValueError):
        generate_quantam_numbers(glyphs="∇⊸≋∇", cycle=1, count=0)
