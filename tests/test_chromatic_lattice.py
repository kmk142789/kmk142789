"""Tests for the chromatic lattice weaving utilities."""
from __future__ import annotations

from echo.chromatic_lattice import (
    ChromaticLattice,
    ChromaticThread,
    render_chromatic_map,
)


def test_chromatic_lattice_weave_generates_nodes() -> None:
    threads = (
        ChromaticThread(name="Aurora", hue=0.84, resonance=0.92, sparks=("glow", "pulse")),
        ChromaticThread(name="Solstice", hue=0.41, resonance=0.68, sparks=("ember",)),
    )
    lattice = ChromaticLattice(base_energy=0.35)

    report = lattice.weave(threads, layers=3)

    assert report.node_count == len(threads) * 3
    assert set(report.dominant_threads) == {"Aurora", "Solstice"}

    aurora_energies = [node.energy for node in report.nodes if node.thread == "Aurora"]
    assert aurora_energies == sorted(aurora_energies)
    assert report.average_energy >= min(aurora_energies)


def test_render_chromatic_map_renders_layers() -> None:
    threads = (
        ChromaticThread(name="Aurora", hue=0.84, resonance=0.92),
    )
    lattice = ChromaticLattice(base_energy=0.25)
    report = lattice.weave(threads, layers=2)

    output = render_chromatic_map(report.nodes)

    assert "Chromatic Lattice Map" in output
    assert "layer 01" in output and "layer 02" in output
    assert "Threads :: Aurora" in output


def test_render_chromatic_map_handles_empty_iterable() -> None:
    assert (
        render_chromatic_map([])
        == "No chromatic nodes woven. Invite new threads to the lattice."
    )
