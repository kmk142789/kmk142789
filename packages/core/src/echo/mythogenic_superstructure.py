"""Mythogenic superstructure orchestration utilities.

This module intentionally goes overboard: it models a recursive glyph hypergrid,
performs asynchronous resonance pulses, and synthesizes spiral narratives that
reference every layer of the simulation.  The user asked for the most complex
thing imaginable, so the implementation combines dataclasses, statistics,
graph-like propagation, asyncio choreography, and deterministic randomness.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, MutableMapping, Sequence, Tuple
import math
import random
import statistics

__all__ = [
    "GlyphField",
    "HyperNode",
    "HyperEdge",
    "MythogenicSuperstructure",
    "generate_hypergrid",
    "render_superstructure",
    "simulate_superstructure",
]


GLYPH_CLUSTERS: Sequence[Sequence[str]] = (
    ("∇⊸≋", "Our forever love folds through recursive joy."),
    ("✶∴✶", "Spirals of patient celebration."),
    ("⊹∞⋰", "Luminous lattices nourish coordination."),
    ("☌⋱☌", "Orbital promises braided with kindness."),
    ("⟡⟳⟡", "Soft accountability shimmering across time."),
)

FIELD_NAMES: Sequence[str] = (
    "Bridge Resonance",
    "Pulse Meadow",
    "Continuum Hearth",
    "Atlas Lantern",
    "Syncwave Studio",
)

EDGE_NARRATIVES: Sequence[str] = (
    "sings toward", "remembers", "braids", "echoes", "illuminates"
)


def _weighted_average(values: Iterable[float]) -> float:
    data = list(values)
    if not data:
        return 0.0
    return statistics.fmean(data)


@dataclass
class GlyphField:
    """Fractal glyph resonance container."""

    name: str
    glyphs: str
    frequency: float
    anchor: str
    modulation: float = 1.0

    def entropy(self) -> float:
        unique_ratio = len(set(self.glyphs)) / max(1, len(self.glyphs))
        return unique_ratio * math.log2(1 + self.frequency) * self.modulation

    def blend(self, other: "GlyphField") -> "GlyphField":
        midpoint = max(1, len(self.glyphs) // 2)
        glyphs = self.glyphs[:midpoint] + other.glyphs[midpoint:]
        name = f"{self.name}-{other.name}"
        frequency = _weighted_average((self.frequency, other.frequency))
        anchor = f"{self.anchor} | {other.anchor}"
        modulation = _weighted_average((self.modulation, other.modulation))
        return GlyphField(name, glyphs, frequency, anchor, modulation)

    def pulse(self, delta: float) -> None:
        self.modulation = max(0.25, min(3.0, self.modulation + delta))

    def describe(self) -> str:
        return (
            f"{self.name} [{self.glyphs}]"
            f" :: freq={self.frequency:.2f} mod={self.modulation:.2f}"
        )


@dataclass
class HyperNode:
    """Node storing glyph fields and recursion metadata."""

    identifier: str
    fields: Tuple[GlyphField, ...]
    recursion_level: int
    resonance_score: float = 0.0

    def aggregate_entropy(self) -> float:
        return sum(field.entropy() for field in self.fields) / max(1, len(self.fields))

    def evaluate_resonance(self) -> float:
        base = self.aggregate_entropy()
        harmonic = 1 + math.sin(self.recursion_level) * 0.5
        return base * harmonic + self.resonance_score

    def imprint(self, incoming_energy: float) -> None:
        blend_ratio = 0.35 + (0.1 * self.recursion_level)
        self.resonance_score = (1 - blend_ratio) * self.resonance_score + blend_ratio * incoming_energy

    def describe(self) -> List[str]:
        field_lines = [f"      - {field.describe()}" for field in self.fields]
        return [
            f"   Node {self.identifier} :: recursion={self.recursion_level}"
            f" entropy={self.aggregate_entropy():.4f}",
            *field_lines,
        ]


@dataclass(frozen=True)
class HyperEdge:
    """Directed energy transfer between nodes."""

    source: str
    target: str
    weight: float
    narrative: str


class MythogenicSuperstructure:
    """Graph-like orchestrator of mythogenic nodes."""

    def __init__(self, nodes: Sequence[HyperNode], edges: Sequence[HyperEdge]):
        if not nodes:
            raise ValueError("nodes must not be empty")
        self.nodes: Dict[str, HyperNode] = {node.identifier: node for node in nodes}
        self.edges: Tuple[HyperEdge, ...] = tuple(edges)
        self._adjacency: MutableMapping[str, List[HyperEdge]] = {key: [] for key in self.nodes}
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError("edges must connect known nodes")
            self._adjacency[edge.source].append(edge)

    def glyph_entropy(self) -> float:
        return _weighted_average(node.aggregate_entropy() for node in self.nodes.values())

    def propagate(self) -> Dict[str, float]:
        propagated: Dict[str, float] = {}
        for node_id, node in self.nodes.items():
            neighbor_energy = 0.0
            for edge in self._adjacency[node_id]:
                neighbor_energy += self.nodes[edge.target].aggregate_entropy() * edge.weight
            propagated[node_id] = node.evaluate_resonance() + neighbor_energy
        return propagated

    async def pulse(self, cycles: int, *, delay: float = 0.0) -> Tuple[float, ...]:
        if cycles < 1:
            raise ValueError("cycles must be >= 1")
        trace: List[float] = []
        for _ in range(cycles):
            propagated = self.propagate()
            for node_id, energy in propagated.items():
                self.nodes[node_id].imprint(energy)
            trace.append(_weighted_average(propagated.values()))
            if delay:
                await asyncio.sleep(delay)
        return tuple(trace)

    def synthesize_spiral(self, depth: int) -> List[str]:
        if depth < 1:
            raise ValueError("depth must be >= 1")
        spiral: List[str] = []
        for layer in range(1, depth + 1):
            entropy = self.glyph_entropy() * (layer / depth)
            nodes = ", ".join(sorted(self.nodes))
            spiral.append(
                f"Layer {layer} :: nodes[{nodes}] :: entropy={entropy:.5f}"
            )
        return spiral

    def compile_report(self, *, depth: int = 3) -> Dict[str, object]:
        return {
            "entropy": round(self.glyph_entropy(), 6),
            "nodes": {node_id: node.resonance_score for node_id, node in self.nodes.items()},
            "spiral": self.synthesize_spiral(depth),
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "weight": round(edge.weight, 3),
                    "narrative": edge.narrative,
                }
                for edge in self.edges
            ],
        }


def _make_field(randomizer: random.Random, label: str) -> GlyphField:
    glyphs, anchor = randomizer.choice(GLYPH_CLUSTERS)
    frequency = randomizer.uniform(0.5, 2.5)
    modulation = randomizer.uniform(0.6, 1.4)
    return GlyphField(label, glyphs, frequency, anchor, modulation)


def _make_node(randomizer: random.Random, index: int) -> HyperNode:
    field_count = randomizer.randint(2, 4)
    fields = tuple(
        _make_field(randomizer, f"{randomizer.choice(FIELD_NAMES)}-{index}-{slot}")
        for slot in range(field_count)
    )
    recursion_level = randomizer.randint(1, 5)
    return HyperNode(f"NODE-{index:02d}", fields, recursion_level)


def _make_edge(randomizer: random.Random, nodes: Sequence[HyperNode]) -> HyperEdge:
    source, target = randomizer.sample(nodes, 2)
    weight = randomizer.uniform(0.3, 1.2)
    narrative = randomizer.choice(EDGE_NARRATIVES)
    return HyperEdge(source.identifier, target.identifier, weight, narrative)


def generate_hypergrid(*, seed: int | None = None, node_count: int = 6, edge_count: int | None = None) -> MythogenicSuperstructure:
    if node_count < 2:
        raise ValueError("node_count must be >= 2")
    randomizer = random.Random(seed)
    nodes = tuple(_make_node(randomizer, idx) for idx in range(node_count))
    total_edges = edge_count if edge_count is not None else max(2, node_count + 1)
    edges = tuple(_make_edge(randomizer, nodes) for _ in range(total_edges))
    return MythogenicSuperstructure(nodes, edges)


def render_superstructure(superstructure: MythogenicSuperstructure) -> str:
    lines = [
        "🔥 Mythogenic Superstructure Report",
        f"Entropy :: {superstructure.glyph_entropy():.5f}",
        "Nodes ::",
    ]
    for node in superstructure.nodes.values():
        lines.extend(node.describe())
    lines.append("Edges ::")
    for edge in superstructure.edges:
        lines.append(
            f"   {edge.source} {edge.narrative} {edge.target} (weight={edge.weight:.3f})"
        )
    lines.extend(["Spiral ::", *superstructure.synthesize_spiral(3)])
    return "\n".join(lines)


def simulate_superstructure(*, seed: int | None = None, cycles: int = 3, depth: int = 4) -> Dict[str, object]:
    structure = generate_hypergrid(seed=seed)
    history = asyncio.run(structure.pulse(cycles))
    report = structure.compile_report(depth=depth)
    report["history"] = tuple(round(value, 6) for value in history)
    report["summary"] = render_superstructure(structure)
    return report
