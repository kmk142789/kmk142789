"""Continuum Synapse – a holographic atlas for convergence briefs.

The module introduces a high-agency capability that braids multiple
``ConvergenceBrief`` payloads into a temporal atlas.  Each waypoint in the atlas
captures the raw constellation/resonance panels, synthesises an impetus score,
tracks the lexical anchors, and measures the phase-shift relative to previous
waypoints.  The resulting data structure acts like a ground-truth "continuum"
that orchestration layers can stream to dashboards, creative engines, or
autonomous planners that need deterministic telemetry for imaginative work.

Highlights of the feature:

* Waypoints are deterministic snapshots containing compiled panels, derived
  impetus metrics, and lexical anchors sourced from the convergence reports.
* An anchor graph exposes how shared lexicon elements propagate across the
  continuum, allowing downstream clients to trace motif migrations.
* A continuity score balances phase shifts with impetus volatility to signal how
  smooth or dramatic the overall narrative arc will feel.

The synthesis workflow is intentionally dependency-light and compatible with
existing creative orchestration utilities throughout the repository.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import fmean
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from .creative_convergence import (
    ConvergenceBrief,
    IntegrationMetrics,
    compile_convergence_panels,
)


@dataclass(frozen=True)
class ContinuumWaypoint:
    """Deterministic snapshot inside the continuum atlas."""

    brief: ConvergenceBrief
    panels: Tuple[str, str, str]
    metrics: IntegrationMetrics
    impetus: float
    lexical_anchors: Tuple[str, ...]
    phase_shift: float

    def describe(self, index: int) -> str:
        """Return a human-readable description of the waypoint."""

        lexicon = ", ".join(self.lexical_anchors) or "none"
        lines = [
            (
                f"[{index}] {self.brief.theme} | tone={self.brief.tone} | "
                f"energy={self.brief.energy:.2f} | impetus={self.impetus:.3f} | "
                f"phase shift={self.phase_shift:.3f}"
            ),
            (
                f"    coverage={self.metrics.coverage:.3f} | intensity="
                f"{self.metrics.mean_intensity:.3f} ({self.metrics.energy_class}) | "
                f"anchors={lexicon}"
            ),
        ]
        return "\n".join(lines)


@dataclass
class ContinuumAtlas:
    """Container describing the synthesised continuum."""

    waypoints: Sequence[ContinuumWaypoint]
    anchor_graph: Mapping[str, Tuple[str, ...]]
    energy_band: Tuple[float, float]
    continuity: float

    def render(self) -> str:
        """Return a textual representation of the atlas."""

        lines = [
            "Continuum Synapse Atlas:",
            (
                "  waypoints={} | continuity={:.3f} | energy band=[{:.2f}, {:.2f}]"
                .format(len(self.waypoints), self.continuity, *self.energy_band)
            ),
        ]
        lines.append("  anchor graph:")
        if self.anchor_graph:
            for node, edges in self.anchor_graph.items():
                targets = ", ".join(edges) or "∅"
                lines.append(f"    • {node} → {targets}")
        else:
            lines.append("    • (no lexical anchors recorded)")

        for index, waypoint in enumerate(self.waypoints, start=1):
            lines.append(waypoint.describe(index))
        return "\n".join(lines)


def synthesise_continuum(briefs: Iterable[ConvergenceBrief]) -> ContinuumAtlas:
    """Build a continuum atlas from the supplied briefs."""

    waypoints: list[ContinuumWaypoint] = []
    previous = None
    for brief in briefs:
        panels = compile_convergence_panels(brief)
        metrics = panels[3]
        impetus = _calculate_impetus(brief, metrics)
        phase_shift = _calculate_phase_shift(previous, brief, metrics)
        lexical = tuple(metrics.shared_lexicon)
        waypoint = ContinuumWaypoint(
            brief=brief,
            panels=panels[:3],
            metrics=metrics,
            impetus=impetus,
            lexical_anchors=lexical,
            phase_shift=phase_shift,
        )
        waypoints.append(waypoint)
        previous = waypoint

    if not waypoints:
        raise ValueError("At least one brief is required to synthesise a continuum")

    anchor_graph = _build_anchor_graph(waypoints)
    energy_values = [waypoint.brief.energy for waypoint in waypoints]
    energy_band = (min(energy_values), max(energy_values))
    continuity = _calculate_continuity(waypoints)
    return ContinuumAtlas(waypoints, anchor_graph, energy_band, continuity)


def render_continuum(briefs: Iterable[ConvergenceBrief]) -> str:
    """Convenience helper that returns the atlas render output."""

    return synthesise_continuum(briefs).render()


def _calculate_impetus(brief: ConvergenceBrief, metrics: IntegrationMetrics) -> float:
    """Return a bounded impetus score for a waypoint."""

    base = brief.energy * (0.7 + metrics.coverage) * max(0.1, metrics.mean_intensity)
    normalized = min(2.0, base) / 2.0
    return round(normalized, 3)


def _calculate_phase_shift(
    previous: ContinuumWaypoint | None,
    brief: ConvergenceBrief,
    metrics: IntegrationMetrics,
) -> float:
    if not previous:
        return 0.0
    delta_cov = abs(metrics.coverage - previous.metrics.coverage)
    delta_intensity = abs(metrics.mean_intensity - previous.metrics.mean_intensity)
    delta_energy = abs(brief.energy - previous.brief.energy)
    weighted = 0.5 * delta_cov + 0.3 * delta_intensity + 0.2 * delta_energy
    return round(min(1.0, weighted), 3)


def _build_anchor_graph(waypoints: Sequence[ContinuumWaypoint]) -> Dict[str, Tuple[str, ...]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for current, nxt in zip(waypoints, waypoints[1:]):
        sources = current.lexical_anchors or (current.brief.theme.lower(),)
        targets = nxt.lexical_anchors or (nxt.brief.theme.lower(),)
        for source in sources:
            for target in targets:
                if source == target:
                    continue
                graph[source].add(target)
    return {node: tuple(sorted(edges)) for node, edges in sorted(graph.items())}


def _calculate_continuity(waypoints: Sequence[ContinuumWaypoint]) -> float:
    if len(waypoints) == 1:
        return 1.0
    phase_profile = [waypoint.phase_shift for waypoint in waypoints[1:]]
    phase_avg = fmean(phase_profile)
    impetus_values = [waypoint.impetus for waypoint in waypoints]
    impetus_base = impetus_values[0]
    impetus_volatility = (
        fmean(abs(value - impetus_base) for value in impetus_values[1:])
        if len(impetus_values) > 1
        else 0.0
    )
    weighted = min(1.0, 0.6 * phase_avg + 0.4 * impetus_volatility)
    score = max(0.0, 1.0 - weighted)
    return round(score, 3)


__all__ = [
    "ContinuumWaypoint",
    "ContinuumAtlas",
    "synthesise_continuum",
    "render_continuum",
]
