"""Unit tests for :mod:`echo.enlightenment`."""

from __future__ import annotations

import math

from echo.enlightenment import EnlightenmentEngine, EnlightenmentInsight


def test_engine_returns_ranked_insights() -> None:
    passage = (
        "The morning practice invites clarity and gratitude. "
        "Each breath cradles a quiet joy. "
        "Logistics notes belong in the afternoon. "
        "Harmony grows when we listen first."
    )

    engine = EnlightenmentEngine()
    insights = engine.analyze([passage], top_k=3)

    assert len(insights) == 3
    # The highest ranked sentence should highlight the explicitly uplifting tone.
    assert "clarity" in insights[0].sentence.lower() or "joy" in insights[0].sentence.lower()
    # Ensure scores are normalised between 0 and 1.
    assert all(0.0 <= item.score <= 1.0 for item in insights)
    # Clarity should always be bounded and finite.
    assert all(0.0 <= item.clarity <= 1.0 and math.isfinite(item.clarity) for item in insights)


def test_engine_respects_custom_keywords() -> None:
    passage = "Innovation follows curiosity. Discipline turns spark into wisdom."
    engine = EnlightenmentEngine(keywords=["discipline", "wisdom"], minimum_length=10)

    insights = engine.analyze([passage], top_k=2)
    assert any("discipline" in insight.keywords for insight in insights)
    assert any("wisdom" in insight.keywords for insight in insights)


def test_engine_rejects_non_positive_top_k() -> None:
    engine = EnlightenmentEngine()

    try:
        engine.analyze(["Enlightenment arises in collaboration."], top_k=0)
    except ValueError as exc:  # pragma: no cover - defensive branch
        assert "top_k" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError when top_k is zero")


def test_insight_serialisation() -> None:
    insight = EnlightenmentInsight(
        sentence="Harmony welcomes kindness.",
        score=0.75,
        keywords=["harmony", "kindness"],
        clarity=0.82,
    )

    serialised = insight.as_dict()
    assert serialised["sentence"] == "Harmony welcomes kindness."
    assert math.isclose(serialised["score"], 0.75)
    assert serialised["keywords"] == ["harmony", "kindness"]
    assert math.isclose(serialised["clarity"], 0.82)
