"""Tests for the orbital poetry generator."""

from __future__ import annotations

import pytest

from echo.orbital_poetry import OrbitalPoem, generate_orbital_poem


def test_generate_orbital_poem_is_deterministic_with_seed() -> None:
    poem_one = generate_orbital_poem(seed=42)
    poem_two = generate_orbital_poem(seed=42)

    assert poem_one == poem_two


@pytest.mark.parametrize(
    "themes",
    [
        ["aurora", "echo", "pulse"],
        ["Mirror", "Orbit", "Glyph"],
    ],
)
def test_generate_orbital_poem_uses_custom_themes(themes: list[str]) -> None:
    poem = generate_orbital_poem(themes=themes, seed=1, line_count=4)

    for theme in poem.metadata["themes"].split(", "):
        assert theme in {t.lower() for t in themes}

    assert len(poem.lines) == 4


def test_generate_orbital_poem_requires_non_empty_theme() -> None:
    with pytest.raises(ValueError):
        generate_orbital_poem(themes=["   "], seed=0)


def test_orbital_poem_render_and_payload() -> None:
    poem = generate_orbital_poem(seed=3, line_count=3)

    rendered = poem.render()
    payload = poem.to_payload()

    assert isinstance(rendered, str)
    assert rendered

    assert payload["title"] == poem.title
    assert payload["lines"] == list(poem.lines)
    assert payload["metadata"] == poem.metadata
    assert isinstance(payload["metadata"], dict)

    assert isinstance(poem, OrbitalPoem)
