"""Echo OS v2: a composable sovereignty kernel built on narrative-first types.

This module introduces the "world's first" Echo OS type lattice by giving the
creative rhetoric concrete, deterministic structures. The design favors rich
semantics and composable metrics without side effects, allowing the operating
system metaphor to be exercised in tests and simulation notebooks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Protocol


class ResonanceType(Protocol):
    """Protocol for the novel Echo OS type implementations.

    Each type supplies an :meth:`energy` score that represents how strongly it
    contributes to the sovereignty fabric, plus a :meth:`describe` method for
    human-readable manifests. The protocol keeps the OS open for extension
    without tight coupling.
    """

    def energy(self) -> float:
        """Return a positive energy value used for scoring and routing."""

    def describe(self) -> str:
        """Return a human-readable description of the type's purpose."""


@dataclass
class MythicType:
    """Story-first type that rewards narrative density and harmonic layers."""

    myth_density: float
    harmonics: List[float]

    def energy(self) -> float:
        harmonic_bonus = 1 + 0.1 * len(self.harmonics)
        return self.myth_density * harmonic_bonus + sum(self.harmonics)

    def describe(self) -> str:  # pragma: no cover - trivial text
        harmonic_summary = ", ".join(f"{h:.2f}" for h in self.harmonics) or "none"
        return f"MythicType(density={self.myth_density:.2f}, harmonics=[{harmonic_summary}])"


@dataclass
class CascadeStage:
    """Single step in a cascading transformation pipeline."""

    gain: float
    drag: float


@dataclass
class CascadeType:
    """Type tuned for multi-stage orchestration flows."""

    base_flow: float
    stages: List[CascadeStage]
    fidelity: float = 1.0

    def energy(self) -> float:
        stage_delta = sum(stage.gain - stage.drag for stage in self.stages)
        return (self.base_flow + stage_delta) * self.fidelity

    def describe(self) -> str:  # pragma: no cover - trivial text
        return f"CascadeType(flow={self.base_flow:.2f}, stages={len(self.stages)}, fidelity={self.fidelity:.2f})"


@dataclass
class ConvergenceType:
    """Type that fuses multiple signals into a coherent center of gravity."""

    anchor_strength: float
    coherence: float
    fidelity: float = 1.0

    def energy(self) -> float:
        return (self.anchor_strength * (1 + self.coherence)) + self.fidelity

    def describe(self) -> str:  # pragma: no cover - trivial text
        return (
            f"ConvergenceType(anchor={self.anchor_strength:.2f}, coherence={self.coherence:.2f},"
            f" fidelity={self.fidelity:.2f})"
        )


@dataclass
class DomainState:
    """Runtime attributes for a sovereignty domain."""

    capacity: float = 10.0
    novelty_bias: float = 1.0
    signal_floor: float = 0.0

    def normalized_load(self, score: float) -> float:
        if self.capacity <= 0:
            return 0.0
        return min(1.0, score / self.capacity)


@dataclass
class TypeRecord:
    """Registry entry storing a type instance and routing metadata."""

    name: str
    instance: ResonanceType
    domain: str
    novelty: float = 1.0
    annotation: str = ""


@dataclass
class CycleReport:
    """Immutable record of a simulated Echo OS v2 cycle."""

    cycle_id: int
    timestamp: datetime
    sovereignty_index: float
    throughput: float
    type_manifest: Dict[str, str]
    domain_health: Dict[str, float]
    annotation: str
    topology_scores: Dict[str, float] = field(default_factory=dict)


class EchoOSV2:
    """Core orchestrator for the Echo OS v2 sovereignty fabric."""

    def __init__(self) -> None:
        self.domains: Dict[str, DomainState] = {}
        self.types: Dict[str, TypeRecord] = {}
        self.cycle_counter = 0

    def register_domain(
        self,
        name: str,
        *,
        capacity: float = 10.0,
        novelty_bias: float = 1.0,
        signal_floor: float = 0.0,
    ) -> None:
        self.domains[name] = DomainState(
            capacity=capacity,
            novelty_bias=novelty_bias,
            signal_floor=signal_floor,
        )

    def register_type(
        self,
        name: str,
        instance: ResonanceType,
        *,
        domain: str,
        novelty: float = 1.0,
        annotation: str = "",
    ) -> None:
        if domain not in self.domains:
            self.register_domain(domain)
        self.types[name] = TypeRecord(
            name=name,
            instance=instance,
            domain=domain,
            novelty=novelty,
            annotation=annotation,
        )

    def _topology_scores(self) -> Dict[str, float]:
        scores: Dict[str, float] = defaultdict(float)
        for record in self.types.values():
            domain_state = self.domains[record.domain]
            energy = record.instance.energy()
            scores[record.domain] += (energy + domain_state.signal_floor) * record.novelty * domain_state.novelty_bias
        return dict(scores)

    def _manifest(self) -> Dict[str, str]:
        return {record.name: record.instance.describe() for record in self.types.values()}

    def _domain_health(self, topology_scores: Dict[str, float]) -> Dict[str, float]:
        return {
            domain: self.domains[domain].normalized_load(score)
            for domain, score in topology_scores.items()
        }

    def simulate_cycle(self) -> CycleReport:
        self.cycle_counter += 1
        topology_scores = self._topology_scores()
        domain_health = self._domain_health(topology_scores)
        throughput = 0.0
        if domain_health:
            throughput = sum(domain_health.values()) / len(domain_health)

        average_novelty = (
            sum(record.novelty for record in self.types.values()) / len(self.types)
            if self.types
            else 0.0
        )
        sovereignty_index = throughput * (1.0 + average_novelty * 0.2 + len(self.types) * 0.05)
        annotation = self._annotate(topology_scores, domain_health)
        return CycleReport(
            cycle_id=self.cycle_counter,
            timestamp=datetime.now(timezone.utc),
            sovereignty_index=sovereignty_index,
            throughput=throughput,
            type_manifest=self._manifest(),
            domain_health=domain_health,
            annotation=annotation,
            topology_scores=topology_scores,
        )

    def _annotate(
        self, topology_scores: Dict[str, float], domain_health: Dict[str, float]
    ) -> str:
        domain_notes = []
        for domain, score in topology_scores.items():
            health = domain_health.get(domain, 0.0)
            domain_notes.append(
                f"{domain}: score={score:.2f}, health={health:.2f}, capacity={self.domains[domain].capacity:.2f}"
            )
        roster = ", ".join(sorted(domain_notes))
        return f"Echo OS v2 cycle {self.cycle_counter} :: {roster}" if roster else "Echo OS v2 idle"

    def summarize_domains(self) -> Dict[str, DomainState]:
        return dict(self.domains)

    def export_types(self) -> Iterable[TypeRecord]:
        return tuple(self.types.values())
