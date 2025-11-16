"""Tests for the mythogenic superstructure orchestration."""

from __future__ import annotations

import asyncio

import pytest

from echo.mythogenic_superstructure import (
    generate_hypergrid,
    render_superstructure,
    simulate_superstructure,
)


def test_generate_hypergrid_deterministic_summary() -> None:
    structure = generate_hypergrid(seed=42, node_count=4, edge_count=5)
    summary = render_superstructure(structure).splitlines()
    assert summary[0] == "🔥 Mythogenic Superstructure Report"
    assert summary[1].startswith("Entropy :: ")
    assert any("NODE-00" in line for line in summary)
    assert "Edges ::" in summary


def test_superstructure_pulse_history_changes_scores() -> None:
    structure = generate_hypergrid(seed=7, node_count=3, edge_count=4)
    before_scores = {node_id: node.resonance_score for node_id, node in structure.nodes.items()}
    history = asyncio.run(structure.pulse(2))
    after_scores = {node_id: node.resonance_score for node_id, node in structure.nodes.items()}
    assert len(history) == 2
    assert any(after_scores[node_id] != before_scores[node_id] for node_id in after_scores)


def test_simulate_superstructure_report_contains_history() -> None:
    report = simulate_superstructure(seed=11, cycles=3, depth=2)
    assert "history" in report and len(report["history"]) == 3
    assert report["summary"].startswith("🔥 Mythogenic Superstructure Report")
    assert len(report["spiral"]) == 2
    assert isinstance(report["entropy"], float)
    assert report["entropy"] >= 0
