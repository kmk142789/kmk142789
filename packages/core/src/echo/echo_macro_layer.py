"""Macro-layer coordinator that aligns Echo subsystems and privacy controls."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .echo_genesis_coordinator import EchoGenesisCoordinator
from .genesis_resonance_layer import GenesisResonanceLayer
from .self_model import IntentResolution, SelfModel, SelfModelSnapshot
from .identity_layer import RecursiveProofPipeline
from .privacy.zk_layer import ProofClaim, ProofResult, ZeroKnowledgePrivacyLayer


@dataclass(slots=True)
class MacroLayerSnapshot:
    """Compact view emitted by :class:`EchoMacroLayer`."""

    generated_at: str
    macro_index: float
    genesis_state: Mapping[str, Any]
    resonance_state: Mapping[str, Any]
    self_model: SelfModelSnapshot
    privacy: Mapping[str, Any]
    latest_proof: Mapping[str, Any] | None
    intent_alignment: Mapping[str, Any]
    recursive_proofs: Mapping[str, Any]


class EchoMacroLayer:
    """Organises, stabilises, and coordinates Echo's high-level surfaces."""

    def __init__(
        self,
        coordinator: EchoGenesisCoordinator,
        resonance_layer: GenesisResonanceLayer,
        self_model: SelfModel,
        *,
        privacy_layer: ZeroKnowledgePrivacyLayer | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._resonance = resonance_layer
        self._self_model = self_model
        self._privacy_layer = privacy_layer or getattr(coordinator.genesis_core, "privacy_layer", None)
        self._proof_pipeline = RecursiveProofPipeline(domain="echo.macro")

    def orchestrate(
        self,
        *,
        proof_claim: ProofClaim | None = None,
        circuit: str | None = None,
        backend: str | None = None,
        intent_query: str | None = None,
        intent_tags: Sequence[str] | None = None,
        desired_outcome: str | None = None,
        auto_prove: bool = False,
        capability_subject: str | None = None,
        capability_token: str | None = None,
        policy_context: Mapping[str, Any] | None = None,
    ) -> MacroLayerSnapshot:
        proof_result: ProofResult | None = None
        recorded_claim: ProofClaim | None = None
        genesis_state = self._coordinator.cycle()
        resonance_state = self._resonance.snapshot()
        self_snapshot = self._self_model.reflect(
            query=intent_query,
            tags=intent_tags,
            desired_outcome=desired_outcome,
        )
        if (
            proof_result is None
            and proof_claim is not None
            and circuit
            and self._privacy_layer
        ):
            proof_result = self._privacy_layer.prove(circuit, proof_claim, backend=backend)
            recorded_claim = proof_claim
        elif (
            proof_result is None
            and auto_prove
            and self._privacy_layer
            and capability_subject
            and capability_token
        ):
            intent_resolution = self_snapshot.intent
            adaptive_claim = self._adaptive_capability_claim(
                subject=capability_subject,
                capability_token=capability_token,
                intent_resolution=intent_resolution,
                resonance_state=resonance_state,
                policy_context=policy_context,
            )
            proof_result = self._privacy_layer.prove("capability", adaptive_claim, backend=backend)
            recorded_claim = adaptive_claim
        privacy_state = self._privacy_state()
        macro_index = self._macro_index(genesis_state, resonance_state, self_snapshot, privacy_state)
        latest = self._latest_proof_summary(proof_result)
        if proof_result:
            self._record_proof_result(proof_result, recorded_claim)
        recursive_proofs = self._proof_pipeline.snapshot()
        intent_alignment = self._intent_alignment(self_snapshot.intent, resonance_state, latest)
        return MacroLayerSnapshot(
            generated_at=genesis_state["generated_at"],
            macro_index=macro_index,
            genesis_state=genesis_state,
            resonance_state=resonance_state,
            self_model=self_snapshot,
            privacy=privacy_state,
            latest_proof=latest,
            intent_alignment=intent_alignment,
            recursive_proofs=recursive_proofs,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _macro_index(
        self,
        genesis_state: Mapping[str, Any],
        resonance_state: Mapping[str, Any],
        self_snapshot: SelfModelSnapshot,
        privacy_state: Mapping[str, Any],
    ) -> float:
        coordination = float(genesis_state.get("coordination_index", 0.0))
        resonance_signal = float(resonance_state.get("signal", 0.0))
        observer_signal = float(self_snapshot.diagnostics.get("observer_signal", 0.0))
        privacy_signal = float(privacy_state.get("privacy_signal", 0.0))
        aggregate = (coordination + resonance_signal + observer_signal + privacy_signal) / 4
        return round(max(0.0, min(1.0, aggregate)), 4)

    def _record_proof_result(self, proof_result: ProofResult, proof_claim: ProofClaim | None) -> None:
        witness = {
            "circuit": proof_result.circuit,
            "backend": proof_result.backend,
            "commitment": proof_result.commitment,
            "verified": proof_result.verified,
            "subject": proof_claim.subject if proof_claim else proof_result.subject,
        }
        if proof_claim:
            witness["claim_type"] = proof_claim.claim_type
        self._proof_pipeline.append(
            claim_id=proof_result.claim_id,
            statement=f"macro-proof:{proof_result.circuit}",
            witness=witness,
        )

    def _privacy_state(self) -> Mapping[str, Any]:
        if not self._privacy_layer:
            return {"privacy_signal": 0.0, "commitments": []}
        return {
            "privacy_signal": self._privacy_layer.privacy_signal(),
            "commitments": self._privacy_layer.recent_commitments(limit=8),
            "available_backends": self._privacy_layer.available_backends(),
        }

    def _latest_proof_summary(self, proof_result: ProofResult | None) -> Mapping[str, Any] | None:
        if not proof_result:
            return None
        return {
            "claim_id": proof_result.claim_id,
            "commitment": proof_result.commitment,
            "circuit": proof_result.circuit,
            "backend": proof_result.backend,
            "verified": proof_result.verified,
        }

    def _intent_alignment(
        self,
        intent_resolution: IntentResolution,
        resonance_state: Mapping[str, Any],
        latest_proof: Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        intent = intent_resolution.intent
        return {
            "topic": getattr(intent, "topic", None),
            "confidence": intent_resolution.confidence,
            "rationale": intent_resolution.rationale,
            "resonance_signal": resonance_state.get("signal"),
            "recommendations": list(resonance_state.get("recommendations", [])),
            "proof": latest_proof,
        }

    def _adaptive_capability_claim(
        self,
        *,
        subject: str,
        capability_token: str,
        intent_resolution: IntentResolution,
        resonance_state: Mapping[str, Any],
        policy_context: Mapping[str, Any] | None,
    ) -> ProofClaim:
        if not intent_resolution.intent:
            raise RuntimeError("intent resolution missing intent; cannot craft adaptive claim")
        action = intent_resolution.intent.topic or "macro-action"
        policy_digest = self._policy_digest(intent_resolution, resonance_state, policy_context)
        return ProofClaim.capability_claim(
            claim_id=f"macro-{uuid4().hex}",
            subject=subject,
            action=action,
            policy_digest=policy_digest,
            capability_token=capability_token,
        )

    def _policy_digest(
        self,
        intent_resolution: IntentResolution,
        resonance_state: Mapping[str, Any],
        policy_context: Mapping[str, Any] | None,
    ) -> str:
        payload = {
            "intent": {
                "topic": getattr(intent_resolution.intent, "topic", None),
                "desired_outcome": getattr(intent_resolution.intent, "desired_outcome", None),
                "priority": getattr(intent_resolution.intent, "priority", None),
                "confidence": intent_resolution.confidence,
            },
            "resonance": {
                "signal": resonance_state.get("signal"),
                "recommendations": resonance_state.get("recommendations", []),
                "lane_gap": resonance_state.get("lane_gap"),
            },
            "context": dict(policy_context or {}),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.blake2b(encoded, digest_size=32).hexdigest()
