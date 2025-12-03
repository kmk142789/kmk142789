"""Tests for :mod:`src.creative_convergence`."""

from __future__ import annotations

import pytest

from src.creative_convergence import (
    ConvergenceBrief,
    compile_convergence_panels,
    compose_convergence_report,
    summarize_convergence,
)


def test_convergence_report_contains_all_panels() -> None:
    brief = ConvergenceBrief(
        theme="signal sanctuary",
        motifs=["aurora lattice", "tidal archive"],
        highlights=["aurora lattice", "community beacon"],
        tone="uplifting",
        energy=1.3,
        constellation_seed=7,
        resonance_seed=11,
    )

    report = compose_convergence_report(brief)

    assert "Constellation Panel" in report
    assert "Resonance Panel" in report
    assert "Integration Panel" in report
    assert "signal sanctuary" in report


def test_convergence_report_is_deterministic_with_seeds() -> None:
    brief = ConvergenceBrief(
        theme="tidal observatory",
        motifs=["memory tide"],
        highlights=["memory tide"],
        tone="reflective",
        energy=1.1,
        constellation_seed=5,
        resonance_seed=5,
    )

    first = compose_convergence_report(brief)
    second = compose_convergence_report(brief)

    assert first == second


def test_integration_panel_surfaces_alignment_gaps() -> None:
    brief = ConvergenceBrief(
        theme="tidal observatory",
        motifs=["memory tide"],
        highlights=["orbital memory"],
        tone="reflective",
        energy=1.0,
        constellation_seed=3,
        resonance_seed=3,
    )

    _, _, integration_panel, metrics = compile_convergence_panels(brief)

    assert "gaps=orbital" in integration_panel
    assert metrics.lexical_gaps == ("orbital",)
    assert 0 <= metrics.alignment_score <= 1


def test_integration_metrics_track_novelty_and_fusion_signal() -> None:
    brief = ConvergenceBrief(
        theme="aurora observatory",
        motifs=["aurora lattice"],
        highlights=["aurora lattice", "quantum beacon"],
        tone="radiant",
        energy=1.2,
        constellation_seed=9,
        resonance_seed=9,
    )

    _, _, _, metrics = compile_convergence_panels(brief)

    assert metrics.novelty_ratio == pytest.approx(0.5)
    assert 0.0 <= metrics.fusion_index <= 1.0
    assert "fusion index" in compose_convergence_report(brief)


def test_integration_metrics_surface_density_coherence_and_watermark() -> None:
    brief = ConvergenceBrief(
        theme="orbital chorus",
        motifs=["orbital chorus", "signal"],
        highlights=["orbital", "chorus"],
        tone="radiant",
        energy=1.0,
        constellation_seed=12,
        resonance_seed=12,
    )

    _, _, panel, metrics = compile_convergence_panels(brief)
    _, _, _, metrics_again = compile_convergence_panels(brief)

    assert 0.0 <= metrics.lexicon_density <= 1.0
    assert 0.0 <= metrics.coherence <= 1.0
    assert metrics.resonance_watermark
    assert metrics.resonance_watermark == metrics_again.resonance_watermark
    assert "watermark" in panel


def test_summary_surfaces_insights_and_headline() -> None:
    brief = ConvergenceBrief(
        theme="aurora observatory",
        motifs=["aurora lattice"],
        highlights=["aurora lattice", "quantum beacon"],
        tone="radiant",
        energy=1.2,
        constellation_seed=9,
        resonance_seed=9,
    )

    summary = summarize_convergence(brief)

    assert "coverage=" in summary["headline"]
    assert summary["insights"].strengths
    assert summary["insights"].recommended_actions
    assert "integration" in summary["panels"]
    assert summary["readiness"] in {"ready", "progressing", "refine"}
    assert summary["readiness_note"]


def test_insights_reflect_lexical_gaps_and_novelty_tension() -> None:
    brief = ConvergenceBrief(
        theme="orbital chorus",
        motifs=["signal"],
        highlights=["orbital", "chorus"],
        tone="reflective",
        energy=1.0,
        constellation_seed=14,
        resonance_seed=14,
    )

    summary = summarize_convergence(brief)
    actions = " ".join(summary["insights"].recommended_actions)

    assert "lexical gaps" in actions.lower()
    assert summary["insights"].risks or summary["insights"].strengths


def test_readiness_classification_surfaces_delivery_signal() -> None:
    brief = ConvergenceBrief(
        theme="signal sanctuary",
        motifs=["aurora lattice", "tidal archive"],
        highlights=["aurora lattice", "community beacon"],
        tone="uplifting",
        energy=1.4,
        constellation_seed=11,
        resonance_seed=21,
    )

    summary = summarize_convergence(brief)

    assert summary["readiness"] == "ready"
    assert "fusion" in summary["readiness_note"].lower()


def test_readiness_detects_fragile_alignment() -> None:
    brief = ConvergenceBrief(
        theme="orbital chorus",
        motifs=["signal"],
        highlights=["orbital", "chorus"],
        tone="reflective",
        energy=1.0,
        constellation_seed=14,
        resonance_seed=14,
    )

    summary = summarize_convergence(brief)

    assert summary["readiness"] == "refine"
    assert "coverage" in summary["readiness_note"].lower() or "coherence" in summary[
        "readiness_note"
    ].lower()
