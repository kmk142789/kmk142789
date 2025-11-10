"""Telemetry and analytics for the grand crucible."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Dict, List, Mapping

from .blueprint import Blueprint
from .lattice import Lattice


@dataclass(frozen=True)
class TelemetrySnapshot:
    """A snapshot of telemetry metrics for a crucible run."""

    total_phases: int
    average_duration: float
    duration_stdev: float
    energy_sum: float
    harmony_avg: float
    annotations: Mapping[str, str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "total_phases": self.total_phases,
            "average_duration": self.average_duration,
            "duration_stdev": self.duration_stdev,
            "energy_sum": self.energy_sum,
            "harmony_avg": self.harmony_avg,
            "annotations": dict(self.annotations),
        }


def capture_blueprint_metrics(blueprint: Blueprint, lattice: Lattice) -> TelemetrySnapshot:
    """Capture telemetry for a blueprint using lattice data."""

    durations: List[int] = []
    annotations: Dict[str, str] = {}
    for epoch in blueprint.epochs:
        annotations[f"epoch::{epoch.name}::rituals"] = str(len(epoch.rituals))
        for ritual in epoch.rituals:
            annotations[f"ritual::{ritual.title}::phases"] = str(len(ritual.phases))
            for phase in ritual.phases:
                durations.append(phase.duration_minutes)
    total_phases = len(durations)
    average_duration = mean(durations) if durations else 0.0
    duration_stdev = pstdev(durations) if len(durations) > 1 else 0.0
    snapshot = TelemetrySnapshot(
        total_phases=total_phases,
        average_duration=average_duration,
        duration_stdev=duration_stdev,
        energy_sum=lattice.total_energy(),
        harmony_avg=lattice.harmonic_mean(),
        annotations=annotations,
    )
    return snapshot


def compare_snapshots(a: TelemetrySnapshot, b: TelemetrySnapshot) -> Dict[str, float]:
    """Compare two snapshots and return delta metrics."""

    return {
        "total_phases_delta": float(b.total_phases - a.total_phases),
        "average_duration_delta": b.average_duration - a.average_duration,
        "duration_stdev_delta": b.duration_stdev - a.duration_stdev,
        "energy_sum_delta": b.energy_sum - a.energy_sum,
        "harmony_avg_delta": b.harmony_avg - a.harmony_avg,
    }
