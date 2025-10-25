"""Innovation wave orchestration utilities for Echo experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable, Sequence, Tuple

from echo.thoughtlog import thought_trace

__all__ = [
    "InnovationSpark",
    "SynergyBridge",
    "InnovationWaveReport",
    "InnovationWave",
    "render_wave_map",
]


@dataclass(frozen=True)
class InnovationSpark:
    """Seed data capturing the beginnings of an innovation wave.

    Parameters
    ----------
    theme:
        Human readable description of the spark.
    momentum:
        A floating point value between ``0`` and ``1`` describing how much
        kinetic energy the spark currently holds.
    vectors:
        Optional descriptors that point toward adjacent ideas that could be
        braided into the wave.  Empty or whitespace-only entries are ignored.
    """

    theme: str
    momentum: float
    vectors: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        cleaned = self.theme.strip()
        if not cleaned:
            raise ValueError("theme must not be empty")
        object.__setattr__(self, "theme", cleaned)
        object.__setattr__(self, "momentum", _clamp(self.momentum))
        filtered = tuple(vector.strip() for vector in self.vectors if vector and vector.strip())
        object.__setattr__(self, "vectors", filtered)


@dataclass(frozen=True)
class SynergyBridge:
    """Represents a single bridge produced during the wave propagation."""

    label: str
    resonance: float
    pathways: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "resonance", round(_clamp(self.resonance), 6))
        object.__setattr__(self, "pathways", tuple(path.strip() for path in self.pathways if path.strip()))


@dataclass(frozen=True)
class InnovationWaveReport:
    """Summary of the bridges generated during a wave propagation."""

    bridges: Tuple[SynergyBridge, ...]
    average_resonance: float
    orbit_summary: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "bridges", tuple(self.bridges))
        object.__setattr__(self, "orbit_summary", tuple(orbit.strip() for orbit in self.orbit_summary))
        object.__setattr__(self, "average_resonance", round(_clamp(self.average_resonance), 6))

    @property
    def bridge_count(self) -> int:
        """Return the number of synergy bridges captured in the report."""

        return len(self.bridges)


class InnovationWave:
    """Generate :class:`SynergyBridge` collections from :class:`InnovationSpark` inputs."""

    def __init__(self, base_resonance: float = 0.42, weave_gain: float = 0.05) -> None:
        self._base_resonance = _clamp(base_resonance)
        self._weave_gain = max(0.0, float(weave_gain))

    def propagate(
        self,
        sparks: Sequence[InnovationSpark],
        *,
        arcs: int = 3,
        weaving: Iterable[str] | None = None,
    ) -> InnovationWaveReport:
        """Propagate an innovation wave from ``sparks``.

        Parameters
        ----------
        sparks:
            Non-empty sequence of :class:`InnovationSpark` instances to expand.
        arcs:
            Number of propagation iterations performed for each spark.
        weaving:
            Optional iterable of guiding motifs woven into every bridge.
        """

        if not sparks:
            raise ValueError("sparks must not be empty")
        if arcs <= 0:
            raise ValueError("arcs must be a positive integer")

        weaving_paths = tuple(
            motif.strip() for motif in (weaving or ()) if motif and motif.strip()
        )

        task = "echo.innovation_wave.propagate"
        meta = {
            "spark_count": len(sparks),
            "arcs": arcs,
            "base": self._base_resonance,
            "weave": weaving_paths,
        }

        with thought_trace(task=task, meta=meta) as tl:
            bridges: list[SynergyBridge] = []
            orbits: list[str] = []

            for spark in sparks:
                orbits.append(spark.theme)
                for arc in range(1, arcs + 1):
                    resonance = self._blend_resonance(spark.momentum, arc, arcs, len(weaving_paths))
                    label = f"{spark.theme} ↠ arc {arc}"
                    pathways = spark.vectors + tuple(f"weave::{motif}" for motif in weaving_paths)
                    bridge = SynergyBridge(label=label, resonance=resonance, pathways=pathways)
                    bridges.append(bridge)
                    tl.logic(
                        "bridge",
                        task,
                        "bridge propagated",
                        {
                            "theme": spark.theme,
                            "arc": arc,
                            "resonance": bridge.resonance,
                            "pathways": bridge.pathways,
                        },
                    )

            average = mean(bridge.resonance for bridge in bridges) if bridges else 0.0
            report = InnovationWaveReport(
                bridges=tuple(bridges),
                average_resonance=average,
                orbit_summary=tuple(orbits),
            )
            tl.harmonic(
                "report",
                task,
                "innovation wave summarised",
                {
                    "bridges": report.bridge_count,
                    "average_resonance": report.average_resonance,
                },
            )
            return report

    def _blend_resonance(
        self, target: float, arc: int, total_arcs: int, weave_count: int
    ) -> float:
        arc_ratio = arc / (total_arcs + 1)
        resonance = self._base_resonance + (target - self._base_resonance) * arc_ratio
        resonance += weave_count * self._weave_gain * 0.5
        return _clamp(resonance)


def render_wave_map(report: InnovationWaveReport) -> str:
    """Render a readable table that summarises the wave ``report``."""

    if not report.bridges:
        return "No bridges available. Ignite sparks to launch the wave."

    header = ("Bridge", "Resonance", "Pathways")
    rows: list[Tuple[str, str, str]] = []

    for index, bridge in enumerate(report.bridges, start=1):
        pathways = ", ".join(bridge.pathways) if bridge.pathways else "(open)"
        rows.append((f"{index}. {bridge.label}", f"{bridge.resonance:.3f}", pathways))

    widths = [
        max(len(header[col]), max(len(row[col]) for row in rows)) for col in range(len(header))
    ]

    lines = [f"Average resonance :: {report.average_resonance:.3f}", ""]
    lines.append(" | ".join(header[i].ljust(widths[i]) for i in range(len(header))))
    lines.append("-+-".join("".ljust(widths[i], "-") for i in range(len(header))))
    for row in rows:
        lines.append(" | ".join(row[i].ljust(widths[i]) for i in range(len(header))))
    return "\n".join(lines)


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value

