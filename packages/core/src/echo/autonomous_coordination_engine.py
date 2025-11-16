"""Autonomous coordination engine fusing identity, proofs, and telemetry."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import inspect
import json
from typing import Any, Mapping, MutableMapping, Sequence

from .echo_macro_layer import EchoMacroLayer, MacroLayerSnapshot
from .identity_layer import RecursiveProofPipeline, SelfAttestingUpgrade
from .sovereign_identity_kernel import CapabilityIdentityKernel

__all__ = [
    "PlanningSignal",
    "SchedulingSignal",
    "UpgradeSignal",
    "CapabilitySignal",
    "CoordinationReport",
    "AutonomousCoordinationEngine",
]


@dataclass(slots=True)
class PlanningSignal:
    """Describe a planning initiative targeted by the coordination engine."""

    initiative: str
    objective: str
    priority: str = "medium"
    owner: str | None = None
    horizon_days: int = 30
    tags: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "initiative": self.initiative,
            "objective": self.objective,
            "priority": self.priority,
            "owner": self.owner,
            "horizon_days": self.horizon_days,
            "tags": list(self.tags),
        }


@dataclass(slots=True)
class SchedulingSignal:
    """Represent a scheduling directive attached to the planning fabric."""

    window: str
    cadence: str = "weekly"
    owners: Sequence[str] = field(default_factory=tuple)
    dependencies: Sequence[str] = field(default_factory=tuple)
    readiness: float = 0.5

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "window": self.window,
            "cadence": self.cadence,
            "owners": list(self.owners),
            "dependencies": list(self.dependencies),
            "readiness": round(max(0.0, min(1.0, self.readiness)), 3),
        }


@dataclass(slots=True)
class UpgradeSignal:
    """Detail a self-attested upgrade aligned with macro telemetry."""

    component: str
    description: str
    status: str = "planned"
    attestation: Mapping[str, Any] | None = None
    additional_context: Mapping[str, Any] | None = None

    def to_dict(self) -> MutableMapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "component": self.component,
            "description": self.description,
            "status": self.status,
        }
        if self.attestation:
            payload["attestation"] = dict(self.attestation)
        if self.additional_context:
            payload["additional_context"] = dict(self.additional_context)
        return payload


@dataclass(slots=True)
class CapabilitySignal:
    """Issued sovereign capability credential for the current coordination cycle."""

    subject: str
    capabilities: Sequence[str]
    credential: Mapping[str, Any]

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "subject": self.subject,
            "capabilities": list(self.capabilities),
            "credential": dict(self.credential),
        }


@dataclass(slots=True)
class CoordinationReport:
    """Structured response emitted by :class:`AutonomousCoordinationEngine`."""

    cycle_id: str
    generated_at: str
    coordination_confidence: float
    identity_state: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    planning: Sequence[Mapping[str, Any]]
    scheduling: Sequence[Mapping[str, Any]]
    upgrades: Sequence[Mapping[str, Any]]
    capability: Mapping[str, Any] | None
    proof_chain: Mapping[str, Any]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "generated_at": self.generated_at,
            "coordination_confidence": self.coordination_confidence,
            "identity_state": dict(self.identity_state),
            "telemetry": dict(self.telemetry),
            "planning": list(self.planning),
            "scheduling": list(self.scheduling),
            "upgrades": list(self.upgrades),
            "capability": None if self.capability is None else dict(self.capability),
            "proof_chain": dict(self.proof_chain),
        }


class AutonomousCoordinationEngine:
    """Fuse sovereign identity, macro-layer telemetry, and recursive proofs."""

    def __init__(
        self,
        identity_kernel: CapabilityIdentityKernel,
        macro_layer: EchoMacroLayer,
        *,
        proof_domain: str = "echo.autonomous",
    ) -> None:
        self._identity_kernel = identity_kernel
        self._macro_layer = macro_layer
        self._proofs = RecursiveProofPipeline(domain=proof_domain)
        self._macro_params = {
            name
            for name in inspect.signature(EchoMacroLayer.orchestrate).parameters
            if name != "self"
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def unify(
        self,
        *,
        planning: Sequence[PlanningSignal | Mapping[str, Any]] | None = None,
        scheduling: Sequence[SchedulingSignal | Mapping[str, Any]] | None = None,
        upgrades: Sequence[UpgradeSignal | Mapping[str, Any] | SelfAttestingUpgrade] | None = None,
        capability_subject: str | None = None,
        requested_capabilities: Sequence[str] | None = None,
        capability_constraints: Mapping[str, Any] | None = None,
        macro_snapshot: MacroLayerSnapshot | None = None,
        macro_kwargs: Mapping[str, Any] | None = None,
    ) -> CoordinationReport:
        """Synthesise a coordination frame anchored in sovereign identity."""

        planning_signals = [self._coerce_planning(signal) for signal in planning or ()]
        scheduling_signals = [self._coerce_scheduling(signal) for signal in scheduling or ()]
        upgrade_signals = [self._coerce_upgrade(signal) for signal in upgrades or ()]

        if macro_snapshot is None:
            filtered_kwargs = self._filter_macro_kwargs(macro_kwargs or {})
            macro_snapshot = self._macro_layer.orchestrate(**filtered_kwargs)

        telemetry_payload = asdict(macro_snapshot)
        identity_snapshot = asdict(self._identity_kernel.snapshot())

        capability_signal: CapabilitySignal | None = None
        if capability_subject and requested_capabilities:
            credential = self._identity_kernel.issue_capability(
                subject_did=capability_subject,
                capabilities=tuple(requested_capabilities),
                constraints=capability_constraints,
            )
            capability_signal = CapabilitySignal(
                subject=capability_subject,
                capabilities=tuple(requested_capabilities),
                credential=credential.to_dict(),
            )

        cycle_id = f"ace:{telemetry_payload['generated_at']}"
        coverage_ratio = self._coverage_ratio(
            planning_signals,
            scheduling_signals,
            upgrade_signals,
            capability_signal,
        )
        coordination_confidence = round(
            min(1.0, (macro_snapshot.macro_index + coverage_ratio) / 2),
            4,
        )

        proof_witness = {
            "cycle_id": cycle_id,
            "macro_index": macro_snapshot.macro_index,
            "planning": [signal.to_dict() for signal in planning_signals],
            "scheduling": [signal.to_dict() for signal in scheduling_signals],
            "upgrades": [signal.to_dict() for signal in upgrade_signals],
            "capability": None if capability_signal is None else capability_signal.to_dict(),
            "identity": identity_snapshot,
        }
        self._proofs.append(
            claim_id=cycle_id,
            statement="autonomous-coordination",
            witness={
                "fingerprint": self._fingerprint(proof_witness),
                "macro_index": macro_snapshot.macro_index,
                "dimensions": {
                    "planning": len(planning_signals),
                    "scheduling": len(scheduling_signals),
                    "upgrades": len(upgrade_signals),
                    "capability": 1 if capability_signal else 0,
                },
            },
        )
        proof_chain = self._proofs.snapshot()

        report = CoordinationReport(
            cycle_id=cycle_id,
            generated_at=telemetry_payload["generated_at"],
            coordination_confidence=coordination_confidence,
            identity_state=identity_snapshot,
            telemetry=telemetry_payload,
            planning=[signal.to_dict() for signal in planning_signals],
            scheduling=[signal.to_dict() for signal in scheduling_signals],
            upgrades=[signal.to_dict() for signal in upgrade_signals],
            capability=None if capability_signal is None else capability_signal.to_dict(),
            proof_chain=proof_chain,
        )
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _coerce_planning(self, signal: PlanningSignal | Mapping[str, Any]) -> PlanningSignal:
        if isinstance(signal, PlanningSignal):
            return signal
        data = dict(signal)
        return PlanningSignal(
            initiative=str(data.get("initiative") or data.get("name") or "unlabeled"),
            objective=str(data.get("objective") or data.get("summary") or ""),
            priority=str(data.get("priority") or "medium"),
            owner=data.get("owner"),
            horizon_days=int(data.get("horizon_days") or data.get("horizon") or 30),
            tags=tuple(data.get("tags") or ()),
        )

    def _coerce_scheduling(self, signal: SchedulingSignal | Mapping[str, Any]) -> SchedulingSignal:
        if isinstance(signal, SchedulingSignal):
            return signal
        data = dict(signal)
        return SchedulingSignal(
            window=str(data.get("window") or data.get("slot") or "unscheduled"),
            cadence=str(data.get("cadence") or data.get("frequency") or "weekly"),
            owners=tuple(data.get("owners") or data.get("stewards") or ()),
            dependencies=tuple(data.get("dependencies") or data.get("links") or ()),
            readiness=float(data.get("readiness") or data.get("confidence") or 0.5),
        )

    def _coerce_upgrade(
        self,
        signal: UpgradeSignal | Mapping[str, Any] | SelfAttestingUpgrade,
    ) -> UpgradeSignal:
        if isinstance(signal, UpgradeSignal):
            return signal
        if isinstance(signal, SelfAttestingUpgrade):
            attestation = signal.to_dict()
            return UpgradeSignal(
                component=attestation["component"],
                description=attestation["description"],
                status="attested",
                attestation=attestation,
            )
        data = dict(signal)
        attestation = data.get("attestation")
        return UpgradeSignal(
            component=str(data.get("component") or data.get("name") or "unspecified"),
            description=str(data.get("description") or ""),
            status=str(data.get("status") or "planned"),
            attestation=dict(attestation) if isinstance(attestation, Mapping) else None,
            additional_context={
                key: value
                for key, value in data.items()
                if key
                not in {"component", "name", "description", "status", "attestation"}
            },
        )

    def _coverage_ratio(
        self,
        planning: Sequence[PlanningSignal],
        scheduling: Sequence[SchedulingSignal],
        upgrades: Sequence[UpgradeSignal],
        capability: CapabilitySignal | None,
    ) -> float:
        dimensions = [
            bool(planning),
            bool(scheduling),
            bool(upgrades),
            capability is not None,
        ]
        active = sum(1 for flag in dimensions if flag)
        return active / len(dimensions)

    def _filter_macro_kwargs(self, kwargs: Mapping[str, Any]) -> MutableMapping[str, Any]:
        return {key: value for key, value in kwargs.items() if key in self._macro_params}

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


