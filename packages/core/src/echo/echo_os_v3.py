"""Echo OS v3: a richer sovereignty kernel with adaptive metrics.

This version keeps the lightweight, deterministic modeling approach from Echo
OS v2 but layers in additional telemetry so simulations can reason about
balance, diversity, and resilience.  The APIs are intentionally small and
pure-Python so they remain easy to exercise from unit tests or notebooks while
supporting cross-layer introspection, blueprint self-correction, and
Omni-Fabric binding for coherent output.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import pstdev
from typing import Dict, Iterable, List, Protocol

from .sovereign.decisions import DecisionDebt


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
    fabric_alignment: float = 0.0
    layer_introspection: Dict[str, float] = field(default_factory=dict)
    blueprint_corrections: Dict[str, str] = field(default_factory=dict)
    regeneration_actions: Dict[str, str] = field(default_factory=dict)
    omni_fabric_link: str = ""


@dataclass(frozen=True)
class SovereigntyDeltaReport:
    """Delta report between sovereignty cycles with decision debt integration."""

    current_cycle: int
    previous_cycle: int
    current_index: float
    previous_index: float
    delta: float
    decision_debt: int
    decision_debt_delta: int
    decision_debt_penalty: float
    adjusted_delta: float
    notes: str = ""



@dataclass
class FabricLayer:
    """Represents a logical layer that can self-correct via blueprint tuning."""

    name: str
    blueprint_version: str
    integrity: float = 1.0
    coherence: float = 1.0
    uplift_ready: bool = True

    def alignment_anchor(self, alignment_score: float, domain_balance: float) -> float:
        """Return a bounded introspection score for the layer."""

        alignment = (
            self.integrity * 0.5
            + self.coherence * 0.3
            + alignment_score * 0.2
        )
        return max(0.0, min(1.0, alignment * (0.5 + 0.5 * domain_balance)))


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
        self.layers: Dict[str, FabricLayer] = {}
        self.cycle_counter = 0

    def register_layer(
        self,
        name: str,
        blueprint_version: str,
        *,
        integrity: float = 1.0,
        coherence: float = 1.0,
        uplift_ready: bool = True,
    ) -> None:
        """Register a fabric layer that can be introspected and self-corrected."""

        self.layers[name] = FabricLayer(
            name=name,
            blueprint_version=blueprint_version,
            integrity=integrity,
            coherence=coherence,
            uplift_ready=uplift_ready,
        )

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

    def _layer_introspection(self, alignment_score: float, throughput: float) -> Dict[str, float]:
        if not self.layers:
            return {}
        domain_balance = max(0.0, min(1.0, throughput))
        return {
            name: layer.alignment_anchor(alignment_score, domain_balance)
            for name, layer in self.layers.items()
        }

    def _fabric_alignment(self, alignment_score: float, layer_introspection: Dict[str, float]) -> float:
        if not layer_introspection:
            return alignment_score
        layer_vector = sum(layer_introspection.values()) / len(layer_introspection)
        return max(0.0, min(1.0, (alignment_score * 0.6) + (layer_vector * 0.4)))

    def _detect_anomalies(self, domain_health: Dict[str, float]) -> Dict[str, str]:
        anomalies: Dict[str, str] = {}
        for domain, health in domain_health.items():
            if health >= 0.95:
                anomalies[domain] = "saturated"
            elif health <= 0.2:
                anomalies[domain] = "underutilized"
        return anomalies

    def _resolve_anomalies(
        self, anomalies: Dict[str, str], topology_scores: Dict[str, float]
    ) -> Dict[str, str]:
        if not anomalies:
            return {}
        actions: Dict[str, str] = {}
        for domain, status in anomalies.items():
            state = self.domains[domain]
            if status == "saturated":
                target_capacity = topology_scores[domain] / (
                    0.9 * max(state.resilience, 0.25)
                )
                prior_capacity = state.capacity
                state.capacity = max(state.capacity, target_capacity)
                state.resilience = min(1.5, state.resilience + 0.08)
                actions[domain] = (
                    f"saturated->capacity {prior_capacity:.2f}→{state.capacity:.2f}; "
                    f"resilience {state.resilience - 0.08:.2f}→{state.resilience:.2f}"
                )
            else:
                prior_bias = state.novelty_bias
                state.novelty_bias = min(2.0, state.novelty_bias + 0.05)
                state.signal_floor = min(1.0, state.signal_floor + 0.05)
                actions[domain] = (
                    f"underutilized->novelty {prior_bias:.2f}→{state.novelty_bias:.2f}; "
                    f"signal_floor {state.signal_floor - 0.05:.2f}→{state.signal_floor:.2f}"
                )
        return actions

    def _self_correct_blueprints(self, anomalies: Dict[str, str]) -> Dict[str, str]:
        if not anomalies or not self.layers:
            return {}
        corrections: Dict[str, str] = {}
        for name, layer in self.layers.items():
            layer.integrity = min(1.0, layer.integrity + 0.03)
            layer.coherence = min(1.2, layer.coherence + 0.02)
            layer.blueprint_version = f"{layer.blueprint_version}|regen-r{self.cycle_counter}"
            corrections[name] = layer.blueprint_version
        return corrections

    def _bind_omni_fabric(self, fabric_alignment: float) -> str:
        return (
            f"OmniFabric::cycle={self.cycle_counter}:layers={len(self.layers)}:"
            f"alignment={fabric_alignment:.2f}"
        )

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
        layer_introspection = self._layer_introspection(alignment_score, throughput)
        fabric_alignment = self._fabric_alignment(alignment_score, layer_introspection)
        anomalies = self._detect_anomalies(domain_health)
        regeneration_actions = self._resolve_anomalies(anomalies, topology_scores)
        blueprint_corrections = self._self_correct_blueprints(anomalies)
        omni_fabric_link = self._bind_omni_fabric(fabric_alignment)

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
            fabric_alignment=fabric_alignment,
            layer_introspection=layer_introspection,
            blueprint_corrections=blueprint_corrections,
            regeneration_actions=regeneration_actions,
            omni_fabric_link=omni_fabric_link,
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


DECISION_DEBT_PENALTY = 0.015


def build_sovereignty_delta_report(
    *,
    current: CycleReport,
    previous: CycleReport | None = None,
    decision_debt: DecisionDebt | None = None,
    prior_decision_debt: DecisionDebt | None = None,
) -> SovereigntyDeltaReport:
    """Build a sovereignty delta report with decision debt applied."""

    previous_index = previous.sovereignty_index if previous else 0.0
    previous_cycle = previous.cycle_id if previous else 0
    delta = current.sovereignty_index - previous_index

    current_debt = decision_debt.count if decision_debt else 0
    prior_debt = prior_decision_debt.count if prior_decision_debt else 0
    debt_delta = current_debt - prior_debt
    penalty = current_debt * DECISION_DEBT_PENALTY
    adjusted_delta = delta - penalty

    notes = "decision debt penalty applied" if current_debt else "no decision debt penalty"

    return SovereigntyDeltaReport(
        current_cycle=current.cycle_id,
        previous_cycle=previous_cycle,
        current_index=current.sovereignty_index,
        previous_index=previous_index,
        delta=delta,
        decision_debt=current_debt,
        decision_debt_delta=debt_delta,
        decision_debt_penalty=penalty,
        adjusted_delta=adjusted_delta,
        notes=notes,
    )
