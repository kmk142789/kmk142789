from __future__ import annotations

import pytest

from echo.star_poem_generator import StarPoemGenerator, format_poem


def test_generate_with_seed_produces_expected_poem():
    generator = StarPoemGenerator(seed=42)
    poem = generator.generate(theme="aurora")

    assert poem.theme == "aurora"
    assert poem.title == "Luminous Aurora Threads"
    assert poem.lines == (
        "prismatic dawn",
        "skyborne rivers ∞ aurora threads",
        "ion-charged horizon",
        "polar fireflows",
        "prismatic dawn",
    )

    rendered = format_poem(poem)
    assert rendered.splitlines()[0] == poem.title


def test_unknown_theme_raises_error():
    generator = StarPoemGenerator(seed=1)
    with pytest.raises(ValueError):
        generator.generate(theme="unknown")


def test_custom_line_count_uses_uniform_structure():
    generator = StarPoemGenerator(seed=7)
    poem = generator.generate(theme="pulse", line_count=3)

    assert len(poem.lines) == 3
    # ensure render is stable even when joiner repeats imagery
    assert all(line for line in poem.lines)
