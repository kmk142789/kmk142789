"""High-order resonance complex simulation utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import random
from statistics import mean
from typing import Mapping, MutableMapping, Sequence


@dataclass(slots=True)
class HarmonicNode:
    """A node participating in the resonance complex network."""

    name: str
    baseline: float
    capacity: float
    tags: tuple[str, ...] = field(default_factory=tuple)
    drift: float = 0.0
    energy: float = field(init=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"node {self.name!r} capacity must be positive")
        self.energy = float(self.baseline)


@dataclass(slots=True)
class HarmonicEdge:
    """Directional or bidirectional transfer edge between nodes."""

    source: str
    target: str
    weight: float
    mode: str = "directed"

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("edge weight must be non-negative")
        if self.mode not in {"directed", "bidirectional"}:
            raise ValueError("mode must be 'directed' or 'bidirectional'")


@dataclass(slots=True)
class ResonanceEvent:
    """Represents a notable event during the simulation of a cycle."""

    node: str
    kind: str
    magnitude: float


@dataclass(slots=True)
class ResonanceSnapshot:
    """State capture for a single simulation cycle."""

    cycle: int
    energies: dict[str, float]
    events: list[ResonanceEvent]
    flux: float


@dataclass(slots=True)
class ResonanceReport:
    """Result of executing a resonance complex simulation."""

    metadata: dict[str, object]
    summary: dict[str, object]
    snapshots: list[ResonanceSnapshot]

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": self.metadata,
            "summary": self.summary,
            "snapshots": [
                {
                    "cycle": snapshot.cycle,
                    "flux": snapshot.flux,
                    "energies": snapshot.energies,
                    "events": [
                        {
                            "node": event.node,
                            "kind": event.kind,
                            "magnitude": event.magnitude,
                        }
                        for event in snapshot.events
                    ],
                }
                for snapshot in self.snapshots
            ],
        }

    def render_summary(self) -> str:
        """Create a multiline summary highlighting key metrics."""

        lines = [
            "Resonance complex simulation",
            f"  cycles            : {self.summary['cycles']}",
            f"  nodes             : {self.summary['nodes']}",
            f"  peak energy       : {self.summary['peak_energy']}",
            f"  average energy    : {self.summary['average_energy']}",
            f"  stability index   : {self.summary['stability_index']}",
            f"  overloaded nodes  : {', '.join(self.summary['overloaded_nodes']) or 'none'}",
        ]
        return "\n".join(lines)


class ResonanceComplex:
    """Encapsulates the rules of a resonance simulation."""

    def __init__(
        self,
        nodes: Sequence[HarmonicNode],
        edges: Sequence[HarmonicEdge],
        *,
        decay: float = 0.15,
        amplification: float = 1.0,
        jitter: float = 0.05,
    ) -> None:
        if not nodes:
            raise ValueError("resonance complex requires at least one node")
        self.nodes: dict[str, HarmonicNode] = {node.name: node for node in nodes}
        if len(self.nodes) != len(nodes):
            raise ValueError("node names must be unique")
        self.edges = list(edges)
        self.decay = decay
        self.amplification = amplification
        self.jitter = jitter
        self._validate_edges()

    def _validate_edges(self) -> None:
        for edge in self.edges:
            if edge.source not in self.nodes:
                raise ValueError(f"edge references unknown source {edge.source!r}")
            if edge.target not in self.nodes:
                raise ValueError(f"edge references unknown target {edge.target!r}")

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ResonanceComplex":
        nodes_payload = payload.get("nodes")
        edges_payload = payload.get("edges")
        if not isinstance(nodes_payload, Sequence) or not nodes_payload:
            raise ValueError("blueprint requires a non-empty 'nodes' array")
        if not isinstance(edges_payload, Sequence):
            edges_payload = []

        nodes = [
            HarmonicNode(
                name=str(item["name"]),
                baseline=float(item.get("baseline", 0.0)),
                capacity=float(item.get("capacity", 1.0)),
                tags=tuple(str(tag) for tag in item.get("tags", [])),
                drift=float(item.get("drift", 0.0)),
            )
            for item in nodes_payload
        ]

        edges = [
            HarmonicEdge(
                source=str(item["source"]),
                target=str(item["target"]),
                weight=float(item.get("weight", 0.0)),
                mode=str(item.get("mode", "directed")),
            )
            for item in edges_payload
        ]

        flux = payload.get("flux", {})
        decay = float(getattr(flux, "get", lambda *_: 0.15)("decay", 0.15))
        amplification = float(getattr(flux, "get", lambda *_: 1.0)("amplification", 1.0))
        jitter = float(getattr(flux, "get", lambda *_: 0.05)("jitter", 0.05))

        return cls(nodes, edges, decay=decay, amplification=amplification, jitter=jitter)

    def simulate(
        self,
        *,
        cycles: int = 6,
        seed: int | None = None,
        drift_scale: float = 0.05,
    ) -> ResonanceReport:
        if cycles <= 0:
            raise ValueError("cycles must be a positive integer")

        rng = random.Random(seed)
        snapshots: list[ResonanceSnapshot] = []
        energy_history: list[float] = []
        overloaded_counts: MutableMapping[str, int] = {name: 0 for name in self.nodes}

        for cycle in range(1, cycles + 1):
            contributions: dict[str, float] = {name: 0.0 for name in self.nodes}
            for edge in self.edges:
                source = self.nodes[edge.source]
                energy = max(0.0, source.energy) * edge.weight
                contributions[edge.target] += energy
                if edge.mode == "bidirectional":
                    contributions[edge.source] += energy * 0.35

            flux = 0.0
            events: list[ResonanceEvent] = []
            for name, node in self.nodes.items():
                delta = contributions[name]
                noise = rng.uniform(-self.jitter, self.jitter) * node.capacity
                drift = rng.uniform(-drift_scale, drift_scale) * node.capacity + node.drift
                updated = (node.energy * (1 - self.decay)) + (delta * self.amplification) + noise + drift
                updated = max(0.0, updated)
                flux += abs(delta)

                if not math.isfinite(updated):
                    updated = node.capacity

                if updated > node.capacity:
                    magnitude = round(updated - node.capacity, 4)
                    overloaded_counts[name] += 1
                    events.append(ResonanceEvent(node=name, kind="overload", magnitude=magnitude))
                    updated = node.capacity + magnitude * 0.1

                node.energy = updated
                energy_history.append(updated)

            snapshot_energies = {name: round(node.energy, 4) for name, node in self.nodes.items()}
            snapshots.append(ResonanceSnapshot(cycle=cycle, energies=snapshot_energies, events=events, flux=round(flux, 4)))

        peak_energy = round(max(energy_history), 4)
        avg_energy = round(mean(energy_history), 4)
        deltas = [
            abs(energy_history[idx] - energy_history[idx - 1])
            for idx in range(1, len(energy_history))
        ]
        stability = 1.0 if not deltas else 1 / (1 + mean(deltas))
        summary = {
            "cycles": cycles,
            "nodes": len(self.nodes),
            "peak_energy": peak_energy,
            "average_energy": avg_energy,
            "stability_index": round(stability, 4),
            "overloaded_nodes": sorted(
                name for name, count in overloaded_counts.items() if count
            ),
        }
        metadata = {
            "seed": seed,
            "decay": self.decay,
            "amplification": self.amplification,
            "jitter": self.jitter,
        }
        return ResonanceReport(metadata=metadata, summary=summary, snapshots=snapshots)


def load_resonance_blueprint(path: Path | str) -> ResonanceComplex:
    """Load a resonance complex blueprint from a JSON file."""

    blueprint_path = Path(path)
    payload = json.loads(blueprint_path.read_text())
    if not isinstance(payload, Mapping):
        raise ValueError("blueprint file must contain a JSON object")
    return ResonanceComplex.from_dict(payload)


def save_resonance_report(report: ResonanceReport, destination: Path | str) -> None:
    """Persist a resonance report as JSON."""

    path = Path(destination)
    path.write_text(json.dumps(report.to_dict(), indent=2))


def build_blueprint_template() -> dict[str, object]:
    """Provide a starter blueprint that can be customised by operators."""

    return {
        "nodes": [
            {"name": "sovereign-core", "baseline": 3.5, "capacity": 8.0, "tags": ["core", "signal"]},
            {"name": "bridge-harmonics", "baseline": 2.1, "capacity": 6.0, "tags": ["bridge"]},
            {"name": "wildlight", "baseline": 1.8, "capacity": 5.5, "tags": ["edge", "creative"]},
        ],
        "edges": [
            {"source": "sovereign-core", "target": "bridge-harmonics", "weight": 0.42, "mode": "bidirectional"},
            {"source": "bridge-harmonics", "target": "wildlight", "weight": 0.58},
            {"source": "wildlight", "target": "sovereign-core", "weight": 0.27},
        ],
        "flux": {"decay": 0.12, "amplification": 1.08, "jitter": 0.04},
    }

