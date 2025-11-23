"""Echo OS v3: a richer sovereignty kernel with adaptive metrics.

This version keeps the lightweight, deterministic modeling approach from Echo
OS v2 but layers in additional telemetry so simulations can reason about
balance, diversity, and resilience.  The APIs are intentionally small and
pure-Python so they remain easy to exercise from unit tests or notebooks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import pstdev
from typing import Dict, Iterable, List, Protocol


class ResonanceType(Protocol):
    """Protocol for Echo OS type implementations.

    Implementations must surface an ``energy`` score plus a human-readable
    description.  The protocol allows Echo OS v3 to remain extensible while
    keeping the core orchestration free of hard dependencies.
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
    resilience: float = 1.0

    def normalized_load(self, score: float) -> float:
        effective_capacity = self.capacity * max(self.resilience, 0.25)
        if effective_capacity <= 0:
            return 0.0
        return min(1.0, score / effective_capacity)


@dataclass
class TypeRecord:
    """Registry entry storing a type instance and routing metadata."""

    name: str
    instance: ResonanceType
    domain: str
    novelty: float = 1.0
    priority: float = 1.0
    annotation: str = ""


@dataclass
class CycleReport:
    """Immutable record of a simulated Echo OS v3 cycle."""

    cycle_id: int
    timestamp: datetime
    sovereignty_index: float
    throughput: float
    type_manifest: Dict[str, str]
    domain_health: Dict[str, float]
    annotation: str
    topology_scores: Dict[str, float] = field(default_factory=dict)
    diversity: float = 0.0
    novelty_index: float = 0.0
    alignment_score: float = 0.0


class EchoOSV3:
    """Core orchestrator for the Echo OS v3 sovereignty fabric.

    Version 3 introduces adaptive metrics to capture how balanced a topology is
    (``alignment_score``) and how widely energy flows across domains
    (``diversity``).  A small feedback hook lets callers adjust domain settings
    between cycles without mutating internal structures directly.
    """

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
        resilience: float = 1.0,
    ) -> None:
        self.domains[name] = DomainState(
            capacity=capacity,
            novelty_bias=novelty_bias,
            signal_floor=signal_floor,
            resilience=resilience,
        )

    def register_type(
        self,
        name: str,
        instance: ResonanceType,
        *,
        domain: str,
        novelty: float = 1.0,
        priority: float = 1.0,
        annotation: str = "",
    ) -> None:
        if domain not in self.domains:
            self.register_domain(domain)
        self.types[name] = TypeRecord(
            name=name,
            instance=instance,
            domain=domain,
            novelty=novelty,
            priority=priority,
            annotation=annotation,
        )

    def ingest_feedback(
        self,
        domain: str,
        *,
        capacity_delta: float = 0.0,
        resilience_delta: float = 0.0,
        signal_floor: float | None = None,
    ) -> None:
        """Apply feedback-driven adjustments to a domain.

        This helper avoids direct mutation in callers while preserving a simple
        API for capacity and resilience tuning between cycles.
        """

        if domain not in self.domains:
            self.register_domain(domain)
        state = self.domains[domain]
        state.capacity += capacity_delta
        state.resilience = max(0.0, state.resilience + resilience_delta)
        if signal_floor is not None:
            state.signal_floor = signal_floor

    def _topology_scores(self) -> Dict[str, float]:
        scores: Dict[str, float] = defaultdict(float)
        for record in self.types.values():
            domain_state = self.domains[record.domain]
            energy = record.instance.energy()
            scores[record.domain] += (
                (energy + domain_state.signal_floor)
                * record.novelty
                * record.priority
                * domain_state.novelty_bias
                * max(domain_state.resilience, 0.1)
            )
        return dict(scores)

    def _manifest(self) -> Dict[str, str]:
        return {record.name: record.instance.describe() for record in self.types.values()}

    def _domain_health(self, topology_scores: Dict[str, float]) -> Dict[str, float]:
        return {
            domain: self.domains[domain].normalized_load(score)
            for domain, score in topology_scores.items()
        }

    def _novelty_index(self) -> float:
        if not self.types:
            return 0.0
        return sum(record.novelty for record in self.types.values()) / len(self.types)

    def _diversity_score(self, topology_scores: Dict[str, float]) -> float:
        if not topology_scores:
            return 0.0
        return len(topology_scores) / max(1, len(self.domains))

    def _alignment_score(self, domain_health: Dict[str, float]) -> float:
        if not domain_health:
            return 0.0
        values = tuple(domain_health.values())
        if len(values) == 1:
            return 1.0
        spread = max(values) - min(values)
        evenness_penalty = pstdev(values)
        return max(0.0, 1.0 - spread * 0.5 - evenness_penalty * 0.25)

    def simulate_cycle(self) -> CycleReport:
        self.cycle_counter += 1
        topology_scores = self._topology_scores()
        domain_health = self._domain_health(topology_scores)
        throughput = 0.0
        if domain_health:
            throughput = sum(domain_health.values()) / len(domain_health)

        novelty_index = self._novelty_index()
        diversity = self._diversity_score(topology_scores)
        alignment_score = self._alignment_score(domain_health)

        sovereignty_index = throughput
        sovereignty_index *= 1.0 + (novelty_index * 0.2) + (diversity * 0.1)
        sovereignty_index *= 0.8 + 0.2 * alignment_score

        annotation = self._annotate(topology_scores, domain_health, diversity, alignment_score)
        return CycleReport(
            cycle_id=self.cycle_counter,
            timestamp=datetime.now(timezone.utc),
            sovereignty_index=sovereignty_index,
            throughput=throughput,
            type_manifest=self._manifest(),
            domain_health=domain_health,
            annotation=annotation,
            topology_scores=topology_scores,
            diversity=diversity,
            novelty_index=novelty_index,
            alignment_score=alignment_score,
        )

    def _annotate(
        self,
        topology_scores: Dict[str, float],
        domain_health: Dict[str, float],
        diversity: float,
        alignment_score: float,
    ) -> str:
        domain_notes = []
        for domain, score in topology_scores.items():
            health = domain_health.get(domain, 0.0)
            domain_notes.append(
                f"{domain}: score={score:.2f}, health={health:.2f}, capacity={self.domains[domain].capacity:.2f}"
            )
        roster = ", ".join(sorted(domain_notes))
        summary_bits = [
            f"diversity={diversity:.2f}",
            f"alignment={alignment_score:.2f}",
            f"types={len(self.types)}",
        ]
        prefix = f"Echo OS v3 cycle {self.cycle_counter}"
        if roster:
            return f"{prefix} :: {roster} :: {'; '.join(summary_bits)}"
        return f"{prefix} idle :: {'; '.join(summary_bits)}"

    def summarize_domains(self) -> Dict[str, DomainState]:
        return dict(self.domains)

    def export_types(self) -> Iterable[TypeRecord]:
        return tuple(self.types.values())
