"""Convergence trajectory analytics and storytelling.

This module layers on top of ``creative_convergence`` to analyse how multiple
briefs evolve over a sequence of phases.  It produces a trajectory snapshot that
captures readiness, fusion momentum, and stability corridors, while surfacing
anomalies when alignment or coherence dip.  The design mirrors other
"digest"-style utilities in the repository: it keeps computation deterministic
and returns rich, human-readable renderings that can be embedded into ops
reports or governance dashboards.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable, Mapping, MutableSequence, Sequence, Tuple

from .creative_convergence import (
    ConvergenceBrief,
    IntegrationMetrics,
    compile_convergence_panels,
    summarize_convergence,
)


@dataclass(frozen=True)
class ConvergenceSnapshot:
    """Represents a single phase within the trajectory."""

    phase: str
    metrics: IntegrationMetrics
    readiness: str
    readiness_note: str
    headline: str

    def alignment_band(self) -> str:
        if self.metrics.alignment_score >= 0.75:
            return "high"
        if self.metrics.alignment_score >= 0.5:
            return "medium"
        return "low"


@dataclass
class ConvergenceTrajectory:
    """Aggregated view of multiple convergence phases."""

    snapshots: Sequence[ConvergenceSnapshot]
    coverage_trend: Sequence[float]
    fusion_trend: Sequence[float]
    coherence_trend: Sequence[float]
    readiness_counts: Mapping[str, int]
    momentum: float
    stability_corridor: Tuple[float, float, float]
    anomaly_flags: Sequence[str]

    def render(self) -> str:
        """Return a human-readable summary of the trajectory."""

        lines: MutableSequence[str] = [
            "Convergence Trajectory:",
            (
                "  coverage trend="
                + ", ".join(f"{value:.3f}" for value in self.coverage_trend)
                + f" | fusion trend={', '.join(f'{value:.3f}' for value in self.fusion_trend)}"
                + f" | coherence trend={', '.join(f'{value:.3f}' for value in self.coherence_trend)}"
            ),
            (
                "  momentum="
                + f"{self.momentum:.3f} | stability corridor="
                + f"min={self.stability_corridor[0]:.3f}, avg={self.stability_corridor[1]:.3f}, max={self.stability_corridor[2]:.3f}"
            ),
            (
                "  readiness counts="
                + ", ".join(f"{state}={count}" for state, count in sorted(self.readiness_counts.items()))
            ),
        ]
        if self.anomaly_flags:
            lines.append("  anomalies: " + "; ".join(self.anomaly_flags))

        for snapshot in self.snapshots:
            metrics = snapshot.metrics
            lines.append(
                (
                    f"- {snapshot.phase}: coverage={metrics.coverage:.3f} | "
                    f"fusion={metrics.fusion_index:.3f} | coherence={metrics.coherence:.3f} "
                    f"| stability={metrics.stability_index:.3f} ({snapshot.alignment_band()})"
                )
            )
            lines.append(f"    readiness={snapshot.readiness} | headline={snapshot.headline}")
            lines.append(f"    note={snapshot.readiness_note}")
        return "\n".join(lines)


def _normalize_phases(phases: Iterable[Tuple[str, ConvergenceBrief]]) -> Sequence[Tuple[str, ConvergenceBrief]]:
    normalized = []
    for phase, brief in phases:
        normalized.append((phase, brief))
    if not normalized:
        raise ValueError("At least one phase is required to build a trajectory")
    return normalized


def _build_snapshot(phase: str, brief: ConvergenceBrief) -> ConvergenceSnapshot:
    _, _, _, metrics = compile_convergence_panels(brief)
    summary = summarize_convergence(brief)
    return ConvergenceSnapshot(
        phase=phase,
        metrics=metrics,
        readiness=summary["readiness"],
        readiness_note=summary["readiness_note"],
        headline=summary["headline"],
    )


def _trend_delta(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return round(values[-1] - values[0], 3)


def _detect_anomalies(snapshots: Sequence[ConvergenceSnapshot]) -> Sequence[str]:
    flags: list[str] = []
    for previous, current in zip(snapshots, snapshots[1:]):
        if current.metrics.coverage < previous.metrics.coverage - 0.15:
            flags.append(
                f"coverage drop from {previous.phase} to {current.phase} "
                f"({previous.metrics.coverage:.3f} -> {current.metrics.coverage:.3f})"
            )
        if current.metrics.coherence < previous.metrics.coherence - 0.15:
            flags.append(
                f"coherence drop from {previous.phase} to {current.phase} "
                f"({previous.metrics.coherence:.3f} -> {current.metrics.coherence:.3f})"
            )
    return tuple(flags)


def build_convergence_trajectory(phases: Iterable[Tuple[str, ConvergenceBrief]]) -> ConvergenceTrajectory:
    """Evaluate a sequence of convergence briefs and return trajectory insights."""

    normalized = _normalize_phases(phases)
    snapshots = tuple(_build_snapshot(phase, brief) for phase, brief in normalized)

    coverage_trend = tuple(snapshot.metrics.coverage for snapshot in snapshots)
    fusion_trend = tuple(snapshot.metrics.fusion_index for snapshot in snapshots)
    coherence_trend = tuple(snapshot.metrics.coherence for snapshot in snapshots)
    readiness_counts = {
        state: sum(1 for snapshot in snapshots if snapshot.readiness == state)
        for state in {snapshot.readiness for snapshot in snapshots}
    }

    delta_coverage = _trend_delta(coverage_trend)
    delta_fusion = _trend_delta(fusion_trend)
    delta_coherence = _trend_delta(coherence_trend)
    momentum = round(0.4 * delta_fusion + 0.35 * delta_coherence + 0.25 * delta_coverage, 3)

    stability_values = [snapshot.metrics.stability_index for snapshot in snapshots]
    stability_corridor = (
        min(stability_values),
        fmean(stability_values),
        max(stability_values),
    )
    anomalies = _detect_anomalies(snapshots)

    return ConvergenceTrajectory(
        snapshots=snapshots,
        coverage_trend=coverage_trend,
        fusion_trend=fusion_trend,
        coherence_trend=coherence_trend,
        readiness_counts=readiness_counts,
        momentum=momentum,
        stability_corridor=stability_corridor,
        anomaly_flags=anomalies,
    )
