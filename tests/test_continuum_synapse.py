"""Tests for the Continuum Synapse atlas."""

from __future__ import annotations

from src.continuum_synapse import render_continuum, synthesise_continuum
from src.creative_convergence import ConvergenceBrief


def _build_briefs() -> list[ConvergenceBrief]:
    return [
        ConvergenceBrief(
            theme="aurora sanctuary",
            motifs=["aurora", "signal sanctuary"],
            highlights=["signal sanctuary", "community"],
            tone="uplifting",
            energy=1.2,
            constellation_seed=5,
            resonance_seed=7,
        ),
        ConvergenceBrief(
            theme="tidal archive",
            motifs=["tidal memory", "continuum"],
            highlights=["continuum", "aurora"],
            tone="contemplative",
            energy=1.5,
            constellation_seed=8,
            resonance_seed=11,
        ),
        ConvergenceBrief(
            theme="signal horizon",
            motifs=["signal horizon", "archive"],
            highlights=["signal", "horizon"],
            tone="radiant",
            energy=1.1,
            constellation_seed=13,
            resonance_seed=17,
        ),
    ]


def test_synthesise_continuum_builds_waypoints_with_metrics():
    atlas = synthesise_continuum(_build_briefs())
    assert len(atlas.waypoints) == 3
    assert atlas.energy_band == (1.1, 1.5)
    assert 0.0 <= atlas.continuity <= 1.0
    for waypoint in atlas.waypoints:
        assert 0.0 <= waypoint.impetus <= 1.0
    assert atlas.waypoints[1].phase_shift > 0.0


def test_anchor_graph_tracks_lexical_bridges():
    atlas = synthesise_continuum(_build_briefs())
    assert atlas.anchor_graph  # should contain entries
    # ensure a motif token such as "signal" connects forward because it is shared
    assert "signal" in atlas.anchor_graph
    assert any(edge in {"continuum", "horizon"} for edge in atlas.anchor_graph["signal"])


def test_render_continuum_outputs_holographic_summary():
    output = render_continuum(_build_briefs())
    assert "Continuum Synapse Atlas" in output
    assert "waypoints=3" in output
    assert "aurora sanctuary" in output
    assert "signal horizon" in output
