"""Macro-layer coordinator that aligns Echo subsystems and privacy controls."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .echo_genesis_coordinator import EchoGenesisCoordinator
from .genesis_resonance_layer import GenesisResonanceLayer
from .self_model import SelfModel, SelfModelSnapshot
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

    def orchestrate(
        self,
        *,
        proof_claim: ProofClaim | None = None,
        circuit: str | None = None,
        backend: str | None = None,
    ) -> MacroLayerSnapshot:
        proof_result: ProofResult | None = None
        if proof_claim and circuit and self._privacy_layer:
            proof_result = self._privacy_layer.prove(circuit, proof_claim, backend=backend)
        genesis_state = self._coordinator.cycle()
        resonance_state = self._resonance.snapshot()
        self_snapshot = self._self_model.reflect()
        privacy_state = self._privacy_state()
        macro_index = self._macro_index(genesis_state, resonance_state, self_snapshot, privacy_state)
        latest = self._latest_proof_summary(proof_result)
        return MacroLayerSnapshot(
            generated_at=genesis_state["generated_at"],
            macro_index=macro_index,
            genesis_state=genesis_state,
            resonance_state=resonance_state,
            self_model=self_snapshot,
            privacy=privacy_state,
            latest_proof=latest,
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
