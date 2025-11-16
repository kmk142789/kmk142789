"""Sovereign coordination kernel that fuses identity, privacy, and macro data."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .echo_macro_layer import EchoMacroLayer, MacroLayerSnapshot
from .identity_layer import RecursiveProofPipeline
from .privacy.zk_layer import ProofClaim, ProofResult, ZeroKnowledgePrivacyLayer
from .sovereign_identity_kernel import (
    CapabilityIdentityKernel,
    IdentityKernelSnapshot,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CapabilityPlan",
    "AutonomyDirective",
    "SovereignKernelReport",
    "SovereignCoordinationKernel",
]


@dataclass(slots=True)
class CapabilityPlan:
    """Structured description of the issued capability bundle."""

    subject: str
    issued_by: str
    capabilities: tuple[str, ...]
    policy_digest: str
    macro_index: float
    constraints: Mapping[str, Any]
    credential: Mapping[str, Any]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "subject": self.subject,
            "issued_by": self.issued_by,
            "capabilities": list(self.capabilities),
            "policy_digest": self.policy_digest,
            "macro_index": self.macro_index,
            "constraints": dict(self.constraints),
            "credential": dict(self.credential),
        }


@dataclass(slots=True)
class AutonomyDirective:
    """Directive surfaced by the coordination kernel."""

    name: str
    description: str
    priority: float
    signals: Mapping[str, Any]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "signals": dict(self.signals),
        }


@dataclass(slots=True)
class SovereignKernelReport:
    """Composite snapshot emitted by :class:`SovereignCoordinationKernel`."""

    generated_at: str
    macro_index: float
    identity: Mapping[str, Any]
    privacy: Mapping[str, Any]
    capability_plan: CapabilityPlan
    recursive_proofs: Mapping[str, Any]
    autonomy_directives: Sequence[AutonomyDirective]
    alignment: Mapping[str, Any]
    capability_proof: Mapping[str, Any] | None = None

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "generated_at": self.generated_at,
            "macro_index": self.macro_index,
            "identity": dict(self.identity),
            "privacy": dict(self.privacy),
            "capability_plan": self.capability_plan.to_dict(),
            "recursive_proofs": dict(self.recursive_proofs),
            "autonomy_directives": [directive.to_dict() for directive in self.autonomy_directives],
            "alignment": dict(self.alignment),
            "capability_proof": dict(self.capability_proof) if self.capability_proof else None,
        }


class SovereignCoordinationKernel:
    """Unifies macro, identity, and privacy data into a sovereign plan."""

    def __init__(
        self,
        identity_kernel: CapabilityIdentityKernel,
        macro_layer: EchoMacroLayer,
        *,
        privacy_layer: ZeroKnowledgePrivacyLayer | None = None,
    ) -> None:
        self._identity = identity_kernel
        self._macro = macro_layer
        candidate_layer = privacy_layer or getattr(macro_layer, "_privacy_layer", None)
        self._privacy_layer: ZeroKnowledgePrivacyLayer | None = candidate_layer
        self._proof_pipeline = RecursiveProofPipeline(domain="echo.sovereign.kernel")

    def coordinate(
        self,
        *,
        subject_did: str,
        requested_capabilities: Sequence[str],
        capability_constraints: Mapping[str, Any] | None = None,
        policy_context: Mapping[str, Any] | None = None,
        intent_query: str | None = None,
        intent_tags: Sequence[str] | None = None,
        desired_outcome: str | None = None,
        prove_capability: bool = True,
        backend: str | None = None,
    ) -> SovereignKernelReport:
        macro_snapshot = self._macro.orchestrate(
            intent_query=intent_query,
            intent_tags=intent_tags,
            desired_outcome=desired_outcome,
        )
        identity_snapshot = self._identity.snapshot()
        plan, capability_token = self._build_capability_plan(
            macro_snapshot,
            identity_snapshot,
            subject_did=subject_did,
            requested_capabilities=requested_capabilities,
            capability_constraints=capability_constraints,
            policy_context=policy_context,
        )
        proof_result = self._prove_capability(plan, capability_token, prove_capability, backend)
        proof_view = self._normalize_proof(proof_result)
        recursive_view = self._compose_recursive_state(macro_snapshot)
        privacy_payload = self._privacy_payload(macro_snapshot, identity_snapshot, proof_view)
        directives = tuple(self._autonomy_directives(macro_snapshot))
        identity_payload = {
            "issuer_did": identity_snapshot.issuer_did,
            "state": dict(identity_snapshot.identity_state),
        }
        report = SovereignKernelReport(
            generated_at=macro_snapshot.generated_at,
            macro_index=macro_snapshot.macro_index,
            identity=identity_payload,
            privacy=privacy_payload,
            capability_plan=plan,
            recursive_proofs=recursive_view,
            autonomy_directives=directives,
            alignment=dict(macro_snapshot.intent_alignment),
            capability_proof=proof_view,
        )
        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_capability_plan(
        self,
        macro_snapshot: MacroLayerSnapshot,
        identity_snapshot: IdentityKernelSnapshot,
        *,
        subject_did: str,
        requested_capabilities: Sequence[str],
        capability_constraints: Mapping[str, Any] | None,
        policy_context: Mapping[str, Any] | None,
    ) -> tuple[CapabilityPlan, str]:
        credential = self._identity.issue_capability(
            subject_did=subject_did,
            capabilities=requested_capabilities,
            constraints=capability_constraints,
        )
        credential_summary = credential.summary()
        credential_summary["signature"] = credential.signature
        policy_digest = self._policy_digest(
            macro_snapshot,
            identity_snapshot,
            capability_constraints=capability_constraints,
            policy_context=policy_context,
        )
        plan = CapabilityPlan(
            subject=subject_did,
            issued_by=self._identity.issuer_did,
            capabilities=tuple(requested_capabilities),
            policy_digest=policy_digest,
            macro_index=macro_snapshot.macro_index,
            constraints=dict(capability_constraints or {}),
            credential=credential_summary,
        )
        self._record_kernel_proof(plan, macro_snapshot)
        return plan, credential.signature

    def _policy_digest(
        self,
        macro_snapshot: MacroLayerSnapshot,
        identity_snapshot: IdentityKernelSnapshot,
        *,
        capability_constraints: Mapping[str, Any] | None,
        policy_context: Mapping[str, Any] | None,
    ) -> str:
        identity_state = dict(identity_snapshot.identity_state)
        proof_state = identity_state.get("proof_pipeline", {})
        payload = {
            "macro_index": macro_snapshot.macro_index,
            "resonance_signal": macro_snapshot.resonance_state.get("signal"),
            "intent_topic": getattr(macro_snapshot.self_model.intent.intent, "topic", None),
            "constraints": dict(capability_constraints or {}),
            "context": dict(policy_context or {}),
            "identity_commitment": proof_state.get("latest_commitment"),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.blake2b(encoded, digest_size=32).hexdigest()

    def _record_kernel_proof(self, plan: CapabilityPlan, macro_snapshot: MacroLayerSnapshot) -> None:
        witness = {
            "macro_commitment": macro_snapshot.recursive_proofs.get("latest_commitment"),
            "capability_nonce": plan.credential.get("nonce"),
            "policy_digest": plan.policy_digest,
            "macro_index": plan.macro_index,
        }
        self._proof_pipeline.append(
            claim_id=f"sovereign-plan-{uuid4().hex}",
            statement="sovereign.capability.plan",
            witness=witness,
        )

    def _prove_capability(
        self,
        plan: CapabilityPlan,
        capability_token: str,
        prove_capability: bool,
        backend: str | None,
    ) -> ProofResult | None:
        if not prove_capability or not self._privacy_layer or not plan.capabilities:
            return None
        claim = ProofClaim.capability_claim(
            claim_id=f"sovereign-cap-{uuid4().hex}",
            subject=plan.subject,
            action=plan.capabilities[0],
            policy_digest=plan.policy_digest,
            capability_token=capability_token,
        )
        try:
            return self._privacy_layer.prove("capability", claim, backend=backend)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("capability proof failed: %s", exc)
            return None

    def _compose_recursive_state(self, macro_snapshot: MacroLayerSnapshot) -> Mapping[str, Any]:
        return {
            "macro": dict(macro_snapshot.recursive_proofs),
            "kernel": self._proof_pipeline.snapshot(),
        }

    def _privacy_payload(
        self,
        macro_snapshot: MacroLayerSnapshot,
        identity_snapshot: IdentityKernelSnapshot,
        proof_view: Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        identity_state = dict(identity_snapshot.identity_state)
        proof_state = identity_state.get("proof_pipeline", {})
        payload = {
            "macro": dict(macro_snapshot.privacy),
            "identity_commitments": list(proof_state.get("recent_claims", [])),
            "shared_command_secret": identity_snapshot.shared_command_secret,
        }
        if proof_view:
            payload["latest_capability_proof"] = proof_view
        return payload

    def _autonomy_directives(self, macro_snapshot: MacroLayerSnapshot) -> Sequence[AutonomyDirective]:
        directives: list[AutonomyDirective] = []
        resolution = macro_snapshot.self_model.intent
        intent_obj = resolution.intent
        resonance = dict(macro_snapshot.resonance_state)
        if intent_obj:
            directives.append(
                AutonomyDirective(
                    name=intent_obj.topic,
                    description=intent_obj.summary,
                    priority=round(max(0.0, min(1.0, resolution.confidence)), 4),
                    signals={
                        "confidence": resolution.confidence,
                        "desired_outcome": intent_obj.desired_outcome,
                        "macro_index": macro_snapshot.macro_index,
                    },
                )
            )
        for recommendation in list(resonance.get("recommendations", []))[:3]:
            directives.append(
                AutonomyDirective(
                    name="resonance",
                    description=recommendation,
                    priority=max(0.2, float(resonance.get("signal", 0.0) or 0.0)),
                    signals={
                        "lane_gap": resonance.get("lane_gap"),
                        "pulse_stability": resonance.get("pulse_stability"),
                    },
                )
            )
        if not directives:
            directives.append(
                AutonomyDirective(
                    name="macro",
                    description="stabilize macro index",
                    priority=macro_snapshot.macro_index,
                    signals={"macro_index": macro_snapshot.macro_index},
                )
            )
        return directives

    def _normalize_proof(self, proof_result: ProofResult | None) -> Mapping[str, Any] | None:
        if not proof_result:
            return None
        return {
            "claim_id": proof_result.claim_id,
            "commitment": proof_result.commitment,
            "circuit": proof_result.circuit,
            "backend": proof_result.backend,
            "verified": proof_result.verified,
            "generated_at": proof_result.generated_at,
        }
