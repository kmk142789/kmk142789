"""Mythogenic pulse engine for orchestrating highly-coupled creative systems."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import statistics
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union
import random


@dataclass
class PulseNode:
    """Represents a single narrative node that can store and amplify charge."""

    key: str
    archetype: str
    charge: float = 0.0
    drift: float = 0.0
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, Union[str, float, Tuple[str, ...]]]:
        return {
            "key": self.key,
            "archetype": self.archetype,
            "charge": self.charge,
            "drift": self.drift,
            "tags": list(self.tags),
        }


@dataclass
class PulseEdge:
    """Directed connection describing how charge flows between nodes."""

    source: str
    target: str
    weight: float = 1.0
    channel: str = "default"

    def as_dict(self) -> Dict[str, Union[str, float]]:
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "channel": self.channel,
        }


Driver = Union[Mapping[str, float], Sequence[Mapping[str, float]], Callable[["MythogenicPulseEngine", int], Mapping[str, float]], None]


class MythogenicPulseEngine:
    """Simulates a mythogenic network with deterministic, explainable updates."""

    def __init__(
        self,
        nodes: Optional[Iterable[PulseNode]] = None,
        edges: Optional[Iterable[PulseEdge]] = None,
        *,
        persistence: float = 0.42,
        attenuation: float = 0.85,
        noise: float = 0.015,
        seed: Optional[int] = None,
    ) -> None:
        self.nodes: Dict[str, PulseNode] = {}
        self.edges: List[PulseEdge] = []
        self.persistence = persistence
        self.attenuation = attenuation
        self.noise = noise
        self.resonance_history: List[Dict[str, float]] = []
        self._rng = random.Random(seed)

        if nodes:
            for node in nodes:
                self.add_node(node)
        if edges:
            for edge in edges:
                self.add_edge(edge)
    def add_node(self, node: PulseNode) -> None:
        if node.key in self.nodes:
            raise ValueError(f"Node '{node.key}' already registered")
        self.nodes[node.key] = PulseNode(
            key=node.key,
            archetype=node.archetype,
            charge=node.charge,
            drift=node.drift,
            tags=tuple(node.tags),
        )

    def add_edge(self, edge: PulseEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("Edges require both nodes to be registered")
        self.edges.append(PulseEdge(edge.source, edge.target, edge.weight, edge.channel))

    @property
    def adjacency(self) -> Mapping[str, List[PulseEdge]]:
        adj: Dict[str, List[PulseEdge]] = {key: [] for key in self.nodes}
        for edge in self.edges:
            adj[edge.target].append(edge)
        return adj

    def _resolve_driver_input(self, driver: Driver, cycle_index: int) -> Mapping[str, float]:
        if driver is None:
            return {}
        if callable(driver):
            return driver(self, cycle_index)
        if isinstance(driver, Mapping):
            return driver
        if isinstance(driver, Sequence):
            if not driver:
                return {}
            idx = cycle_index % len(driver)
            return driver[idx]
        raise TypeError("driver must be Mapping, Sequence, callable, or None")

    def _apply_noise(self) -> float:
        return self._rng.uniform(-self.noise, self.noise)

    def step(self, intensities: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
        signal = intensities or {}
        contributions: Dict[str, float] = {key: 0.0 for key in self.nodes}
        for edge in self.edges:
            source_charge = self.nodes[edge.source].charge
            contributions[edge.target] += source_charge * edge.weight

        updates: Dict[str, float] = {}
        for node in self.nodes.values():
            base = signal.get(node.key, signal.get(node.archetype, 0.0))
            carry = node.charge * self.persistence
            inbound = contributions[node.key] * self.attenuation
            noisy_signal = base + carry + inbound + node.drift + self._apply_noise()
            new_charge = math.tanh(noisy_signal)
            updates[node.key] = new_charge

        for key, value in updates.items():
            self.nodes[key].charge = value

        metrics = self._record_metrics(signal)
        return metrics

    def _record_metrics(self, signal: Mapping[str, float]) -> Dict[str, float]:
        charges = [node.charge for node in self.nodes.values()]
        if not charges:
            report = {"energy": 0.0, "coherence": 1.0, "entropy": 0.0, "pulse": 0.0}
        else:
            energy = sum(abs(c) for c in charges) / len(charges)
            variance = statistics.pvariance(charges) if len(charges) > 1 else 0.0
            coherence = 1.0 / (1.0 + variance)
            entropy = -sum(
                (abs(c) if c else 0.0) * math.log(abs(c) + 1e-9)
                for c in charges
            ) / len(charges)
            pulse = sum(signal.values())
            report = {
                "energy": round(energy, 6),
                "coherence": round(coherence, 6),
                "entropy": round(entropy, 6),
                "pulse": round(pulse, 6),
            }
        self.resonance_history.append(report)
        return report

    def run(self, cycles: int, driver: Driver = None) -> List[Dict[str, float]]:
        if cycles < 1:
            raise ValueError("cycles must be >= 1")
        history: List[Dict[str, float]] = []
        for idx in range(cycles):
            intensities = self._resolve_driver_input(driver, idx)
            history.append(self.step(intensities))
        return history

    def graph_signature(self) -> Dict[str, float]:
        node_count = len(self.nodes)
        if node_count == 0:
            return {"density": 0.0, "branching": 0.0, "channels": 0.0}
        channel_counts: Dict[str, int] = {}
        out_degree: Dict[str, int] = {key: 0 for key in self.nodes}
        for edge in self.edges:
            out_degree[edge.source] += 1
            channel_counts[edge.channel] = channel_counts.get(edge.channel, 0) + 1
        density = len(self.edges) / (node_count ** 2)
        branching = sum(out_degree.values()) / node_count
        channels = len(channel_counts)
        return {
            "density": round(density, 6),
            "branching": round(branching, 6),
            "channels": float(channels),
        }

    def export_state(self) -> Dict[str, object]:
        return {
            "nodes": [node.as_dict() for node in self.nodes.values()],
            "edges": [edge.as_dict() for edge in self.edges],
            "history": list(self.resonance_history),
            "signature": self.graph_signature(),
        }

    def to_json(self) -> str:
        return json.dumps(self.export_state(), indent=2, sort_keys=True)

    @classmethod
    def from_blueprint(
        cls,
        blueprint: Mapping[str, object],
        *,
        persistence: float = 0.42,
        attenuation: float = 0.85,
        noise: float = 0.015,
        seed: Optional[int] = None,
    ) -> "MythogenicPulseEngine":
        nodes_payload = blueprint.get("nodes", [])
        edges_payload = blueprint.get("edges", [])
        nodes = [
            PulseNode(
                key=entry["key"],
                archetype=entry.get("archetype", "generic"),
                charge=float(entry.get("charge", 0.0)),
                drift=float(entry.get("drift", 0.0)),
                tags=tuple(entry.get("tags", [])),
            )
            for entry in nodes_payload
        ]
        edges = [
            PulseEdge(
                source=entry["source"],
                target=entry["target"],
                weight=float(entry.get("weight", 1.0)),
                channel=entry.get("channel", "default"),
            )
            for entry in edges_payload
        ]
        return cls(
            nodes,
            edges,
            persistence=persistence,
            attenuation=attenuation,
            noise=noise,
            seed=seed,
        )

