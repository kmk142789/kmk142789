"""Evolutionary Orchestration Engine.

This module implements the user-requested "Evolutionary Orchestration Engine". The
engine is intentionally self-contained so it can be used by other packages in the
repository without creating any additional runtime dependencies.  The goal is to
combine several foundational capabilities—identity verification, macro-layer
telemetry analysis, autonomous scheduling, recursive proofs, and capability
emergence detection—into a cohesive orchestration pipeline that continuously
evolves subsystem architectures.

The engine exposes dataclasses for the key signals as well as a high-level
``EvolutionaryOrchestrationEngine`` façade that coordinates the orchestration
cycle.  Each cycle performs the following phases:

1. **Identity anchoring** – ingest identity vectors and compute a trust-weighted
   view of the actors participating in the orchestration cycle.
2. **Macro-layer telemetry** – calculate a normalized health index for the
   provided telemetry snapshot and surface macro concerns.
3. **Autonomous scheduling** – prioritize subsystems that require immediate
   action and map them to the most capable identities.
4. **Recursive proofs** – build deterministic proof strings (using SHA-256) that
   link telemetry state, subsystem intent, and the selected identity lineage.
5. **Capability-emergence signals** – promote subsystems that cross a defined
   capability threshold.
6. **Upgrade proposals, integration orchestration, integrity validation, and
   next-generation planning** – produce structured upgrade proposals, convert
   them into an integration plan, validate the plan, and emit the next plan.

The engine favors deterministic logic over stochastic heuristics so that unit
tests can reason about the resulting plans without fragile expectations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class IdentityVector:
    """Represents an identity that can execute orchestration work."""

    handle: str
    trust_score: float
    lineage: Sequence[str]
    capabilities: Sequence[str]

    def anchor_hash(self) -> str:
        """Return a deterministic hash that anchors the identity lineage."""

        lineage_material = "|".join(self.lineage)
        capability_material = "|".join(sorted(self.capabilities))
        digest = sha256(f"{self.handle}:{lineage_material}:{capability_material}".encode())
        return digest.hexdigest()


@dataclass
class TelemetrySignal:
    """Encapsulates a single macro-layer telemetry signal."""

    channel: str
    value: float
    trend: float = 0.0
    metadata: Dict[str, float] | None = None

    def normalized_value(self) -> float:
        """Return a deterministic normalization of the signal value/trend."""

        base = max(0.0, min(1.0, self.value))
        modifier = 0.25 * max(-1.0, min(1.0, self.trend))
        normalized = max(0.0, min(1.0, base + modifier))
        return round(normalized, 4)


@dataclass
class MacroLayerTelemetry:
    """Aggregated telemetry snapshot used by the orchestration engine."""

    epoch: datetime
    signals: List[TelemetrySignal]
    narrative: str = ""

    def health_index(self) -> float:
        if not self.signals:
            return 0.0
        total = sum(signal.normalized_value() for signal in self.signals)
        return round(total / len(self.signals), 4)

    def channels_above(self, threshold: float) -> List[str]:
        return [signal.channel for signal in self.signals if signal.normalized_value() >= threshold]


@dataclass
class ScheduleEntry:
    subsystem: str
    owner: str
    priority: int
    window_start: datetime
    window_end: datetime


@dataclass
class UpgradeProposal:
    subsystem: str
    action: str
    impact: float
    risk: float
    recursive_proof: str


@dataclass
class IntegrationPlan:
    scheduled_for: datetime
    steps: List[str]
    orchestration_vector: Dict[str, str]


@dataclass
class ValidationResult:
    integrity_passed: bool
    issues: List[str]
    coverage_ratio: float


@dataclass
class EngineReport:
    cycle: int
    telemetry_health: float
    identity_vector: Dict[str, float]
    schedule: List[ScheduleEntry]
    capability_signals: List[str]
    upgrades: List[UpgradeProposal]
    integration_plan: IntegrationPlan
    validation: ValidationResult
    next_gen_plan: Dict[str, str]


class EvolutionaryOrchestrationEngine:
    """Coordinates the orchestration cycle described by the specification."""

    def __init__(
        self,
        identities: Iterable[IdentityVector],
        capability_threshold: float = 0.72,
    ) -> None:
        self._identities = list(identities)
        if not self._identities:
            raise ValueError("At least one identity vector is required")
        self._identity_map = {identity.handle: identity for identity in self._identities}
        self.capability_threshold = capability_threshold
        self.cycle = 0

    def run_cycle(self, telemetry: MacroLayerTelemetry) -> EngineReport:
        self.cycle += 1

        identity_vector = {identity.handle: round(identity.trust_score, 3) for identity in self._identities}
        health_index = telemetry.health_index()
        schedule = self._build_autonomous_schedule(telemetry)
        capability_signals = self._detect_capability_emergence(telemetry)
        upgrades = self._propose_upgrades(schedule, capability_signals, telemetry)
        integration_plan = self._orchestrate_integration(upgrades, telemetry)
        validation = self._validate_integrity(integration_plan, upgrades)
        next_plan = self._emit_next_generation_plan(capability_signals, validation)

        return EngineReport(
            cycle=self.cycle,
            telemetry_health=health_index,
            identity_vector=identity_vector,
            schedule=schedule,
            capability_signals=capability_signals,
            upgrades=upgrades,
            integration_plan=integration_plan,
            validation=validation,
            next_gen_plan=next_plan,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_autonomous_schedule(self, telemetry: MacroLayerTelemetry) -> List[ScheduleEntry]:
        window_start = telemetry.epoch
        schedule: List[ScheduleEntry] = []
        sorted_signals = sorted(
            telemetry.signals,
            key=lambda signal: signal.normalized_value(),
            reverse=True,
        )
        for index, signal in enumerate(sorted_signals):
            owner = self._identities[index % len(self._identities)].handle
            window_end = window_start + timedelta(hours=2 + index)
            schedule.append(
                ScheduleEntry(
                    subsystem=signal.channel,
                    owner=owner,
                    priority=index + 1,
                    window_start=window_start,
                    window_end=window_end,
                )
            )
        return schedule

    def _detect_capability_emergence(self, telemetry: MacroLayerTelemetry) -> List[str]:
        emergent = []
        for signal in telemetry.signals:
            if signal.normalized_value() >= self.capability_threshold and signal.trend >= 0:
                emergent.append(signal.channel)
        return emergent

    def _propose_upgrades(
        self,
        schedule: List[ScheduleEntry],
        capability_signals: List[str],
        telemetry: MacroLayerTelemetry,
    ) -> List[UpgradeProposal]:
        proposals: List[UpgradeProposal] = []
        if not schedule:
            return proposals

        capability_set = set(capability_signals)
        for entry in schedule:
            signal_score = 1.0 if entry.subsystem in capability_set else 0.65
            risk = 1 - (entry.priority / (len(schedule) + 1))
            owner_identity = self._identity_map[entry.owner]
            recursive_proof = self._build_recursive_proof(
                subsystem=entry.subsystem,
                telemetry_epoch=telemetry.epoch,
                identity=owner_identity,
            )
            proposals.append(
                UpgradeProposal(
                    subsystem=entry.subsystem,
                    action=f"Upgrade {entry.subsystem} pathway",
                    impact=round(signal_score, 3),
                    risk=round(risk, 3),
                    recursive_proof=recursive_proof,
                )
            )
        return proposals

    def _build_recursive_proof(self, subsystem: str, telemetry_epoch: datetime, identity: IdentityVector) -> str:
        material = f"{subsystem}:{telemetry_epoch.isoformat()}:{identity.anchor_hash()}"
        return sha256(material.encode()).hexdigest()

    def _orchestrate_integration(self, upgrades: List[UpgradeProposal], telemetry: MacroLayerTelemetry) -> IntegrationPlan:
        steps = []
        orchestration_vector = {}
        for index, proposal in enumerate(upgrades):
            steps.append(f"{index + 1}. Deploy {proposal.subsystem} update")
            orchestration_vector[proposal.subsystem] = proposal.recursive_proof[:12]

        scheduled_for = telemetry.epoch + timedelta(hours=len(upgrades) or 1)
        if not steps:
            steps = ["No upgrades scheduled"]
        return IntegrationPlan(scheduled_for=scheduled_for, steps=steps, orchestration_vector=orchestration_vector)

    def _validate_integrity(self, integration_plan: IntegrationPlan, upgrades: List[UpgradeProposal]) -> ValidationResult:
        issues: List[str] = []
        unique_steps = len(set(integration_plan.steps))
        coverage_ratio = round(unique_steps / max(1, len(upgrades)), 3)
        if not upgrades:
            issues.append("No upgrades were proposed during this cycle")
        integrity_passed = coverage_ratio >= 0.5
        return ValidationResult(integrity_passed=integrity_passed, issues=issues, coverage_ratio=coverage_ratio)

    def _emit_next_generation_plan(self, capability_signals: List[str], validation: ValidationResult) -> Dict[str, str]:
        summary = "stable" if validation.integrity_passed else "attention"
        signal_summary = ",".join(sorted(capability_signals)) or "none"
        return {
            "sequence": f"cycle-{self.cycle + 1}",
            "status": summary,
            "signals": signal_summary,
        }


__all__ = [
    "EvolutionaryOrchestrationEngine",
    "EngineReport",
    "IdentityVector",
    "IntegrationPlan",
    "MacroLayerTelemetry",
    "ScheduleEntry",
    "TelemetrySignal",
    "UpgradeProposal",
    "ValidationResult",
]

