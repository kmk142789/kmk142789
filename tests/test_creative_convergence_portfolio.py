import pytest

from src.creative_convergence import ConvergenceBrief, compile_convergence_panels
from src.creative_convergence_portfolio import (
    build_portfolio_digest,
    summarise_portfolio,
)


def _sample_brief(theme: str, highlight: str, *, energy: float = 1.0) -> ConvergenceBrief:
    return ConvergenceBrief(
        theme=theme,
        motifs=["aurora lattice"],
        highlights=[highlight],
        tone="uplifting",
        energy=energy,
        constellation_seed=5,
        resonance_seed=7,
    )


def test_compile_convergence_panels_exposes_metrics():
    brief = _sample_brief("signal sanctuary", "aurora lattice")
    _, _, _, metrics = compile_convergence_panels(brief)
    assert metrics.coverage == pytest.approx(1.0)
    assert metrics.shared_lexicon == ("aurora", "lattice")
    assert metrics.mean_intensity > 0
    assert metrics.energy_class
    assert metrics.lexical_gaps == ()
    assert 0 <= metrics.alignment_score <= 1


def test_portfolio_digest_tracks_leaders_and_renders_summary():
    briefs = [
        _sample_brief("signal sanctuary", "aurora lattice", energy=1.2),
        _sample_brief("tidal archive", "tidal anchor", energy=0.9),
    ]
    digest = build_portfolio_digest(briefs)
    assert len(digest.entries) == 2
    assert digest.coverage_leader.theme == "signal sanctuary"
    assert digest.average_alignment > 0
    assert 0 <= digest.average_fusion <= 1
    assert digest.fusion_leader.theme in {brief.theme for brief in briefs}
    assert digest.consistency_index > 0
    text = digest.render()
    assert "Convergence Portfolio Digest" in text
    assert "coverage leader" in text
    assert "fusion pulse" in text
    assert "average alignment" in text
    assert "gap leader" in text
    assert "tidal archive" in text


def test_summarise_portfolio_matches_digest_render():
    briefs = [_sample_brief("signal", "aurora lattice")]
    digest = build_portfolio_digest(briefs)
    assert summarise_portfolio(briefs) == digest.render()


def test_portfolio_digest_requires_briefs():
    with pytest.raises(ValueError):
        build_portfolio_digest([])


def test_portfolio_digest_exposes_alignment_band_and_gap_hotspots():
    briefs = [
        _sample_brief("signal sanctuary", "aurora lattice", energy=1.1),
        _sample_brief("tidal archive", "tidal anchor", energy=0.9),
        _sample_brief("tidal archive", "anchor line", energy=0.8),
    ]

    digest = build_portfolio_digest(briefs)

    assert digest.coverage_span == pytest.approx(1.0)

    expected_band = (
        "high" if digest.average_alignment >= 0.75 else "medium" if digest.average_alignment >= 0.5 else "low"
    )
    assert digest.alignment_band == expected_band

    assert digest.gap_hotspots[0] == ("anchor", 2)
    assert any(phrase == "tidal" for phrase, _ in digest.gap_hotspots)
