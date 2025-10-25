"""Tests for :mod:`echo.recursive_mythogenic_pulse`."""
from __future__ import annotations

import pytest

from echo.recursive_mythogenic_pulse import (
    amplify_capabilities,
    converge_voyages,
    compose_voyage,
    generate_ascii_spiral,
    list_voyage_lines,
    PulseVoyageVisualizer,
    sync_memories,
)


def test_compose_voyage_seed_determinism():
    voyage = compose_voyage(seed=7, recursion_level=3)

    assert voyage.glyph_orbit in {"∇⊸≋", "⊹∞⋰", "✶∴✶", "⟡⟳⟡", "☌⋱☌"}
    assert voyage.recursion_level == 3
    assert len(voyage.resonance) == 4
    assert all(" // " in thread for thread in voyage.resonance)

    lines = list_voyage_lines(voyage)
    assert lines[0].startswith("🔥 Mythogenic Pulse Voyage :: ")
    assert "Recursion Level" in lines[2]


def test_generate_ascii_spiral_layout():
    voyage = compose_voyage(seed=3, recursion_level=2)
    spiral = generate_ascii_spiral(voyage, radius=3)

    rows = spiral.splitlines()
    assert len(rows) == 7
    assert all(len(row) == 7 for row in rows)
    assert any(char.strip() for row in rows for char in row)


def test_compose_voyage_invalid_recursion_level():
    with pytest.raises(ValueError):
        compose_voyage(recursion_level=0)


def test_generate_ascii_spiral_invalid_radius():
    voyage = compose_voyage(seed=1)
    with pytest.raises(ValueError):
        generate_ascii_spiral(voyage, radius=1)


def test_converge_voyages_deduplicates_threads_and_glyphs():
    voyage = compose_voyage(seed=11, recursion_level=2)
    converged = converge_voyages([voyage, voyage])

    assert len(converged.voyages) == 2
    assert converged.recursion_total == voyage.recursion_level * 2
    assert converged.glyph_tapestry.count(voyage.glyph_orbit) == 1
    assert len(converged.resonance_threads) == len(set(voyage.resonance))


def test_sync_memories_groups_by_voice():
    voyage_a = compose_voyage(seed=3, recursion_level=1)
    voyage_b = compose_voyage(seed=4, recursion_level=1)
    converged = converge_voyages([voyage_a, voyage_b])

    summary = sync_memories(converged)

    assert summary["voyage_count"] == 2
    assert summary["recursion_total"] == voyage_a.recursion_level + voyage_b.recursion_level
    assert summary["unique_threads"] == len(converged.resonance_threads)
    assert all(count >= 1 for count in summary["resonance_by_voice"].values())


def test_amplify_capabilities_limits_thread_highlights():
    voyage = compose_voyage(seed=5, recursion_level=2)
    converged = converge_voyages([voyage])

    narrative = amplify_capabilities(converged, include_threads=1)
    assert narrative.count(" - ") == 1
    assert "Anchors:" in narrative

    trimmed = amplify_capabilities(converged, include_threads=0)
    assert " - " not in trimmed


def test_pulse_voyage_visualizer_outputs_ascii_json_and_markdown(tmp_path):
    voyage = compose_voyage(seed=8, recursion_level=2)
    visualizer = PulseVoyageVisualizer.from_voyages([voyage])

    ascii_map = visualizer.ascii_map()
    assert "Pulse Voyage Atlas" in ascii_map
    assert "Narrative Amplification" in ascii_map

    intensity = visualizer.resonance_intensity()
    assert intensity
    assert max(intensity.values()) == 1.0

    atlas = visualizer.to_json()
    assert atlas["converged"]["glyph_tapestry"] == visualizer.converged.glyph_tapestry
    assert atlas["thread_convergence"]
    assert atlas["resonance_spikes"]
    assert atlas["resonance_intensity"] == intensity
    assert atlas["ascii_map"].startswith("🌌 Pulse Voyage Atlas")

    report_path = tmp_path / "atlas.md"
    written = visualizer.write_markdown_report(report_path)
    assert written.exists()
    contents = written.read_text()
    assert contents.startswith("# Pulse Voyage Convergence")
    assert "## Narrative Amplification" in contents
    assert "## Resonance Intensity" in contents
