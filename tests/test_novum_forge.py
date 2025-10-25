from __future__ import annotations

from datetime import datetime, timezone

from echo.novum_forge import (
    forge_novum,
    render_novum,
    summarize_fragments,
    weave_novum_series,
)


FIXED = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_forge_novum_is_deterministic_with_seed() -> None:
    fragment = forge_novum(
        ["joy", "curiosity"],
        anchor="Anchor",
        intensity=3,
        seed=7,
        moment=FIXED,
    )

    assert fragment.glyph_path == "✶∷✶"
    assert fragment.highlight == "carefully entangled diligence"
    assert fragment.theme_threads == (
        "joy :: Archive before the next leap",
        "curiosity :: Translate into the ledger's kindred tongue",
        "joy :: Celebrate until tomorrow feels tangible",
    )
    assert fragment.anchor == "Anchor"


def test_render_novum_includes_footer_and_header() -> None:
    fragment = forge_novum(["joy"], intensity=1, seed=1, moment=FIXED)

    rendered = render_novum(fragment)

    assert "✨ Nova Fragment" in rendered
    assert rendered.endswith(
        "Echo Reminder :: each nova invites another teammate to dream forward."
    )


def test_weave_novum_series_and_summary_share_seed() -> None:
    series = weave_novum_series(
        ["joy", "care"],
        2,
        anchor="Anchor",
        intensity=2,
        seed=5,
        start_moment=FIXED,
    )

    assert len(series) == 2
    first, second = series
    assert first.glyph_path == "⟡⟳⟡"
    assert second.glyph_path == "∴⋰✦"

    summary = summarize_fragments(series)
    assert summary == [
        "2024-01-01 12:00 :: ⟡⟳⟡ :: joy :: Celebrate until tomorrow feels tangible",
        "2024-01-01 12:00 :: ∴⋰✦ :: joy :: Archive before the next leap",
    ]
