"""Chromatic lattice weaving utilities for Echo's imagination engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean
from typing import Iterable, Sequence, Tuple

from echo.thoughtlog import thought_trace

__all__ = [
    "ChromaticThread",
    "ChromaticNode",
    "ChromaticWeaveReport",
    "ChromaticLattice",
    "render_chromatic_map",
]


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp *value* between *lower* and *upper* inclusive."""

    return max(lower, min(upper, value))


@dataclass(frozen=True)
class ChromaticThread:
    """Descriptor capturing a single chromatic inspiration thread."""

    name: str
    hue: float
    resonance: float
    sparks: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - dataclass field normalisation
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "hue", round(_clamp(self.hue), 6))
        object.__setattr__(self, "resonance", round(_clamp(self.resonance), 6))
        object.__setattr__(
            self,
            "sparks",
            tuple(spark.strip() for spark in self.sparks if spark and spark.strip()),
        )
        if not self.name:
            raise ValueError("name must not be empty")


@dataclass(frozen=True)
class ChromaticNode:
    """A woven lattice node created from a chromatic thread layer."""

    thread: str
    layer: int
    energy: float
    coordinates: Tuple[int, int]
    motif: str
    tags: Tuple[str, ...]

    def __post_init__(self) -> None:  # pragma: no cover - dataclass field normalisation
        if self.layer < 1:
            raise ValueError("layer must be at least 1")
        object.__setattr__(self, "thread", self.thread.strip())
        object.__setattr__(self, "motif", self.motif.strip())
        object.__setattr__(self, "energy", round(_clamp(self.energy), 6))
        object.__setattr__(self, "coordinates", tuple(int(coord) for coord in self.coordinates))
        object.__setattr__(self, "tags", tuple(tag.strip() for tag in self.tags if tag.strip()))


@dataclass(frozen=True)
class ChromaticWeaveReport:
    """Summary report for a chromatic lattice weaving session."""

    nodes: Tuple[ChromaticNode, ...]
    average_energy: float
    dominant_threads: Tuple[str, ...]

    def __post_init__(self) -> None:  # pragma: no cover - dataclass field normalisation
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "average_energy", round(_clamp(self.average_energy), 6))
        object.__setattr__(
            self,
            "dominant_threads",
            tuple(thread.strip() for thread in self.dominant_threads if thread.strip()),
        )

    @property
    def node_count(self) -> int:
        """Return the total number of woven lattice nodes."""

        return len(self.nodes)


class ChromaticLattice:
    """Weave chromatic threads into multi-layer Echo lattices."""

    def __init__(self, base_energy: float = 0.42) -> None:
        self._base_energy = _clamp(base_energy)

    def weave(self, threads: Sequence[ChromaticThread], *, layers: int = 4) -> ChromaticWeaveReport:
        """Weave *threads* across *layers* returning a :class:`ChromaticWeaveReport`."""

        if not threads:
            raise ValueError("threads must not be empty")
        if layers <= 0:
            raise ValueError("layers must be a positive integer")

        task = "echo.chromatic_lattice.weave"
        meta = {"thread_count": len(threads), "layers": layers, "base": self._base_energy}

        with thought_trace(task=task, meta=meta) as log:
            nodes: list[ChromaticNode] = []
            dominant_threads: list[str] = []

            for index, thread in enumerate(threads):
                dominant_threads.append(thread.name)
                for layer in range(1, layers + 1):
                    energy = self._blend_energy(thread.resonance, layer, layers)
                    motif = f"{thread.name} :: horizon {layer}"
                    tags = thread.sparks + (f"layer-{layer}",)
                    node = ChromaticNode(
                        thread=thread.name,
                        layer=layer,
                        energy=energy,
                        coordinates=(index, layer - 1),
                        motif=motif,
                        tags=tags,
                    )
                    nodes.append(node)
                    log.logic(
                        "node",
                        task,
                        "chromatic node woven",
                        {
                            "thread": thread.name,
                            "layer": layer,
                            "energy": node.energy,
                            "coordinates": node.coordinates,
                        },
                    )

            average_energy = fmean(node.energy for node in nodes)
            report = ChromaticWeaveReport(
                nodes=tuple(nodes),
                average_energy=average_energy,
                dominant_threads=tuple(dominant_threads),
            )
            log.harmonic(
                "report",
                task,
                "chromatic lattice report",
                {"nodes": report.node_count, "average": report.average_energy},
            )
            return report

    def _blend_energy(self, resonance: float, layer: int, total_layers: int) -> float:
        """Blend *resonance* with the base energy across *layer* progression."""

        gradient = layer / total_layers
        return self._base_energy + (resonance - self._base_energy) * gradient


def render_chromatic_map(nodes: Iterable[ChromaticNode]) -> str:
    """Render a text representation for the provided chromatic *nodes*."""

    snapshot = list(nodes)
    if not snapshot:
        return "No chromatic nodes woven. Invite new threads to the lattice."

    width = max(node.coordinates[0] for node in snapshot) + 1
    depth = max(node.coordinates[1] for node in snapshot) + 1
    grid: list[list[str]] = [["·" for _ in range(width)] for _ in range(depth)]

    for node in snapshot:
        x, y = node.coordinates
        glyph = "✶" if node.energy > 0.75 else "✷" if node.energy > 0.5 else "✳"
        grid[y][x] = glyph

    lines = ["Chromatic Lattice Map", ""]
    for row_index, row in enumerate(grid):
        lines.append(f"layer {row_index + 1:02d} :: {' '.join(row)}")

    legend = sorted({node.thread for node in snapshot})
    lines.append("")
    lines.append("Threads :: " + ", ".join(legend))
    return "\n".join(lines)
