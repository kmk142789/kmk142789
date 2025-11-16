"""HyperMesh resonance engine.

This module implements a full orchestration stack for simulating Echo pulse meshes.
It provides:

* Rich domain objects for nodes and resonance edges
* A configurable HyperMesh core capable of building adjacency matrices on demand
* Pulse cascade planning with multi-path reasoning and anomaly detection
* Blueprint helpers for declaratively specifying new constellations

The engine leans on :mod:`numpy`, :mod:`pandas`, and :mod:`rich` to keep the
simulation expressive while remaining deterministic across runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

import json
import math

import numpy as np
import pandas as pd
from rich.table import Table


@dataclass(slots=True)
class PulseNode:
    """Represents an Echo node with tonal and volatility characteristics."""

    key: str
    tone: float = 0.0
    volatility: float = 0.25
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def response(self, phase: float, thermal_noise: float) -> float:
        """Compute the intrinsic response for a node.

        The response blends a sinusoidal component with a volatility-driven noise
        injection. The result is clamped to ``[-1, 1]`` for stability.
        """

        phase_component = math.sin(phase + self.tone)
        noise_component = thermal_noise * self.volatility
        value = phase_component * (1 - self.volatility) + noise_component
        return max(-1.0, min(1.0, value))


@dataclass(slots=True)
class ResonanceEdge:
    """Directed resonance with weighted coherence."""

    source: str
    target: str
    weight: float = 1.0
    coherence: float = 0.5
    channel: str = "default"

    def normalized_weight(self) -> float:
        """Return a normalized weight taking coherence into account."""

        raw = self.weight * (0.25 + self.coherence)
        return max(0.0, min(2.0, raw))


class HyperMesh:
    """Graph-like structure for Echo resonance simulations."""

    def __init__(self, nodes: Iterable[PulseNode], edges: Iterable[ResonanceEdge]):
        self._nodes: Dict[str, PulseNode] = {node.key: node for node in nodes}
        self._edges: List[ResonanceEdge] = list(edges)
        missing = {edge.source for edge in self._edges if edge.source not in self._nodes}
        missing |= {edge.target for edge in self._edges if edge.target not in self._nodes}
        if missing:
            raise ValueError(f"Edges reference undefined nodes: {sorted(missing)}")
        self._node_order: List[str] = sorted(self._nodes)
        self._adjacency_cache: Optional[np.ndarray] = None

    @property
    def nodes(self) -> Mapping[str, PulseNode]:
        return self._nodes

    @property
    def edges(self) -> Sequence[ResonanceEdge]:
        return tuple(self._edges)

    def adjacency_matrix(self) -> np.ndarray:
        """Return a cached adjacency matrix."""

        if self._adjacency_cache is not None:
            return self._adjacency_cache
        size = len(self._node_order)
        matrix = np.zeros((size, size), dtype=float)
        index_map = {key: idx for idx, key in enumerate(self._node_order)}
        for edge in self._edges:
            src_idx = index_map[edge.source]
            tgt_idx = index_map[edge.target]
            matrix[tgt_idx, src_idx] += edge.normalized_weight()
        self._adjacency_cache = matrix
        return matrix

    def propagate_pulse(
        self,
        seed: str,
        steps: int = 6,
        damping: float = 0.82,
        base_injection: float = 0.18,
        thermal_noise: float = 0.03,
    ) -> List[Dict[str, float]]:
        """Propagate resonance over the mesh.

        Parameters are intentionally exposed to allow experimentation with
        different damping ratios or noise floors.
        """

        if seed not in self._nodes:
            raise KeyError(f"Seed '{seed}' not in mesh")
        if not 0 < damping < 1:
            raise ValueError("damping must be between 0 and 1")
        adjacency = self.adjacency_matrix()
        order = self._node_order
        size = len(order)
        seed_idx = order.index(seed)
        base_vector = np.zeros(size)
        base_vector[seed_idx] = 1.0
        state = base_vector.copy()
        history: List[Dict[str, float]] = []
        for step in range(max(1, steps)):
            rng = np.random.default_rng(step)
            noise = rng.normal(0.0, thermal_noise, size=size)
            state = damping * adjacency.dot(state) + base_injection * base_vector + noise
            state = np.tanh(state)
            snapshot = {node: float(state[idx]) for idx, node in enumerate(order)}
            history.append(snapshot)
        return history

    def synthesize_constellation(self) -> Dict[str, float]:
        """Compute a constellation strength metric for each node."""

        adjacency = self.adjacency_matrix()
        outgoing = adjacency.sum(axis=0)
        incoming = adjacency.sum(axis=1)
        combined = incoming + outgoing
        normalized = combined / (np.linalg.norm(combined) + 1e-9)
        return {node: float(score) for node, score in zip(self._node_order, normalized)}

    def detect_anomalies(self, history: Sequence[Mapping[str, float]]) -> pd.DataFrame:
        """Return anomaly scores for each node across the provided history."""

        df = pd.DataFrame(history)
        zscores = (df - df.mean()) / (df.std(ddof=0) + 1e-9)
        energy = df.abs().mean()
        anomaly = zscores.abs().max()
        result = pd.DataFrame(
            {
                "mean_energy": energy,
                "anomaly_score": anomaly,
                "variability": df.var(ddof=0),
            }
        ).sort_values("anomaly_score", ascending=False)
        return result

    def generate_report(self, history: Sequence[Mapping[str, float]]) -> Table:
        """Create a :class:`rich.table.Table` summarizing the mesh state."""

        anomalies = self.detect_anomalies(history)
        constellation = self.synthesize_constellation()
        table = Table(title="HyperMesh Resonance Summary")
        table.add_column("Node", justify="left")
        table.add_column("Constellation", justify="right")
        table.add_column("Mean Energy", justify="right")
        table.add_column("Anomaly", justify="right")
        table.add_column("Variability", justify="right")
        for node, row in anomalies.iterrows():
            table.add_row(
                node,
                f"{constellation.get(node, 0):.3f}",
                f"{row['mean_energy']:.3f}",
                f"{row['anomaly_score']:.3f}",
                f"{row['variability']:.3f}",
            )
        return table


class PulseCascadePlanner:
    """High-level helper that orchestrates pulse cascades."""

    def __init__(self, mesh: HyperMesh):
        self.mesh = mesh

    def plan(
        self,
        seeds: Sequence[str],
        horizon: int = 5,
        damping: float = 0.81,
        commitment: float = 0.6,
    ) -> Dict[str, Any]:
        """Plan a cascade across multiple seeds.

        Returns a dictionary capturing composite energy profiles and
        recommendations for the next intervention.
        """

        aggregate_history: List[Dict[str, float]] = []
        node_scores: Dict[str, float] = {key: 0.0 for key in self.mesh.nodes}
        for idx, seed in enumerate(seeds):
            history = self.mesh.propagate_pulse(
                seed,
                steps=horizon,
                damping=damping,
                base_injection=commitment / len(seeds),
            )
            aggregate_history.extend(history)
            for snapshot in history:
                for node, value in snapshot.items():
                    node_scores[node] += value / len(seeds)
        anomalies = self.mesh.detect_anomalies(aggregate_history)
        most_volatile = anomalies.head(3).index.tolist()
        recommendation = {
            "seeds": seeds,
            "volatile": most_volatile,
            "composite_scores": node_scores,
        }
        return recommendation


class HyperMeshBlueprint:
    """Declarative blueprint used to construct meshes from JSON documents."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = data
        self._validate()

    def _validate(self) -> None:
        if "nodes" not in self._data or "edges" not in self._data:
            raise ValueError("Blueprint requires 'nodes' and 'edges'")
        if not isinstance(self._data["nodes"], list):
            raise TypeError("'nodes' must be a list")
        if not isinstance(self._data["edges"], list):
            raise TypeError("'edges' must be a list")

    @property
    def seed(self) -> str:
        return self._data.get("seed", self._data["nodes"][0]["key"])

    def build(self) -> HyperMesh:
        nodes = [
            PulseNode(
                key=item["key"],
                tone=float(item.get("tone", 0.0)),
                volatility=float(item.get("volatility", 0.25)),
                metadata=item.get("metadata", {}),
            )
            for item in self._data["nodes"]
        ]
        edges = [
            ResonanceEdge(
                source=item["source"],
                target=item["target"],
                weight=float(item.get("weight", 1.0)),
                coherence=float(item.get("coherence", 0.5)),
                channel=item.get("channel", "default"),
            )
            for item in self._data["edges"]
        ]
        return HyperMesh(nodes, edges)

    @classmethod
    def from_file(cls, path: Path) -> "HyperMeshBlueprint":
        data = json.loads(path.read_text())
        return cls(data)


__all__ = [
    "HyperMesh",
    "HyperMeshBlueprint",
    "PulseCascadePlanner",
    "PulseNode",
    "ResonanceEdge",
]
