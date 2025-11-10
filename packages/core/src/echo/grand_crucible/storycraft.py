"""Narrative synthesis utilities for the grand crucible."""
from __future__ import annotations

from collections import defaultdict
from textwrap import indent
from typing import Dict, List

from .blueprint import Blueprint, Epoch
from .lattice import Lattice


def craft_epoch_digest(epoch: Epoch) -> str:
    """Generate a textual digest for a single epoch."""

    ritual_summaries = [
        f"- {ritual.title} ({len(ritual.phases)} phases, duration {ritual.total_duration()} min)"
        for ritual in epoch.rituals
    ]
    annotations = ", ".join(f"{k}={v}" for k, v in sorted(epoch.annotations.items())) or "none"
    ritual_block = indent("\n".join(ritual_summaries), "  ")
    return (
        f"Epoch: {epoch.name}\n"
        f"Purpose: {epoch.purpose}\n"
        f"Annotations: {annotations}\n"
        f"Rituals:\n{ritual_block}"
    )


def craft_blueprint_overview(blueprint: Blueprint, lattice: Lattice) -> str:
    """Craft a high-level overview combining blueprint and lattice data."""

    header = (
        f"Title: {blueprint.title}\n"
        f"Architect: {blueprint.architect}\n"
        f"Epochs: {len(blueprint.epochs)}\n"
        f"Total Duration: {blueprint.total_duration()} minutes\n"
        f"Lattice Summary: {lattice.summarize()}"
    )
    epoch_sections = [craft_epoch_digest(epoch) for epoch in blueprint.epochs]
    metadata_section = "Metadata:\n" + indent(
        "\n".join(f"{key}: {value}" for key, value in sorted(blueprint.metadata.items())) or "<empty>",
        "  ",
    )
    return "\n\n".join([header] + epoch_sections + [metadata_section])


def build_phase_heatmap(blueprint: Blueprint) -> Dict[str, List[int]]:
    """Aggregate phase counts per ritual to support heatmap visualizations."""

    heatmap: Dict[str, List[int]] = defaultdict(list)
    for epoch in blueprint.epochs:
        for ritual in epoch.rituals:
            heatmap[epoch.name].append(len(ritual.phases))
    return dict(heatmap)


def render_heatmap_ascii(heatmap: Dict[str, List[int]]) -> str:
    """Render a simple ASCII heatmap representation."""

    lines: List[str] = []
    for epoch_name, counts in heatmap.items():
        bars = ["█" * min(count, 40) or "·" for count in counts]
        lines.append(f"{epoch_name}: {' '.join(bars)}")
    return "\n".join(lines)


def storyline_from_lattice(lattice: Lattice) -> List[str]:
    """Translate lattice points into a narrative beat sequence."""

    storyline: List[str] = []
    for point in lattice:
        storyline.append(
            f"[{point.epoch}] {point.ritual} → {point.phase} | depth {point.depth} | "
            f"energy {point.energy:.2f} | harmony {point.harmony:.2f}"
        )
    return storyline
