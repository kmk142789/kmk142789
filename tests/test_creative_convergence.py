"""Tests for :mod:`src.creative_convergence`."""

from __future__ import annotations

from src.creative_convergence import ConvergenceBrief, compose_convergence_report


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
