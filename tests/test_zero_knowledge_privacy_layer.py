"""Tests for the Zero-Knowledge Privacy Layer and macro-layer wiring."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo.echo_genesis_core import EchoGenesisCore, SubsystemProbe
from echo.echo_genesis_coordinator import EchoGenesisCoordinator
from echo.echo_macro_layer import EchoMacroLayer
from echo.genesis_resonance_layer import GenesisResonanceLayer
from echo.continuum_resonance_field import (
    ContinuumResonanceReport,
    LaneResonance,
    PulseDrift,
)
from echo.self_model import (
    IntentResolver,
    MemoryUnifier,
    ObserverSubsystem,
    SelfModel,
)
from echo.semantic_negotiation import NegotiationIntent
from echo.privacy.zk_layer import (
    CapabilityCircuit,
    EventCommitmentCircuit,
    HashCommitmentBackend,
    KeyOwnershipCircuit,
    ProofClaim,
    ZeroKnowledgePrivacyLayer,
)


class _StaticField:
    def __init__(self, report: ContinuumResonanceReport) -> None:
        self._report = report

    def scan(self) -> ContinuumResonanceReport:
        return self._report


def _privacy_layer() -> ZeroKnowledgePrivacyLayer:
    layer = ZeroKnowledgePrivacyLayer()
    layer.register_backend(HashCommitmentBackend())
    layer.register_circuit(KeyOwnershipCircuit())
    layer.register_circuit(CapabilityCircuit())
    layer.register_circuit(EventCommitmentCircuit())
    return layer


def _simple_probe() -> SubsystemProbe:
    return SubsystemProbe(
        name="telemetry",
        kind="telemetry",
        focus="stability",
        weight=1.0,
        probe=lambda: {"signal": 0.82, "health": 0.8},
    )


def test_zero_knowledge_flow_integrates_with_genesis_core(tmp_path: Path) -> None:
    privacy = _privacy_layer()
    core = EchoGenesisCore(
        probes=[_simple_probe()],
        state_dir=tmp_path / "core",
        privacy_layer=privacy,
    )
    claim = ProofClaim.key_ownership(
        claim_id="claim-key",
        subject="guardian",
        public_key="pk-demo",
        private_material="secret-abc",
    )

    result = core.request_proof("key_ownership", claim)
    assert result.verified

    architecture = core.synthesize()
    assert "privacy" in architecture
    assert result.commitment in architecture["privacy"]["recent_commitments"]
    receipts = architecture["privacy"]["receipts"]
    assert receipts[-1]["claim_id"] == "claim-key"


def test_zero_knowledge_failure_paths(tmp_path: Path) -> None:
    privacy = _privacy_layer()
    claim_missing = ProofClaim(
        claim_id="missing",
        claim_type="key_ownership",
        subject="node",
        statement={"public_key": "pk"},
        private_inputs={},
    )
    with pytest.raises(ValueError):
        privacy.prove("key_ownership", claim_missing)

    valid_claim = ProofClaim.key_ownership(
        claim_id="valid",
        subject="node",
        public_key="pk2",
        private_material="material",
    )
    result = privacy.prove("key_ownership", valid_claim)
    result.proof["sealed_witness"] = "tampered"
    assert not privacy.verify(result)

    with pytest.raises(ValueError):
        privacy.prove("key_ownership", valid_claim, backend="snark")


def test_macro_layer_wiring_with_privacy(tmp_path: Path) -> None:
    privacy = _privacy_layer()
    core = EchoGenesisCore(
        probes=[_simple_probe()],
        state_dir=tmp_path / "core",
        privacy_layer=privacy,
    )
    coordinator = EchoGenesisCoordinator(core, state_dir=tmp_path / "coordinator")
    coordinator.link_subsystem(
        "telemetry",
        provider=object(),
        kind="telemetry",
        focus="stability",
        extractor=lambda _: {"signal": 0.8},
    )

    pulse = PulseDrift(
        total_events=3,
        cadence_seconds=120.0,
        latest_timestamp=None,
        latest_message=None,
        channel_counts={"pulse": 3},
        stability_index=0.8,
    )
    lanes = [
        LaneResonance(
            lane="docs",
            activity_ratio=0.5,
            doc_ratio=0.6,
            code_ratio=0.4,
            freshness_days=1.0,
            resonance_index=0.7,
        )
    ]
    report = ContinuumResonanceReport(
        root=tmp_path,
        generated_at=datetime.now(timezone.utc),
        lanes=lanes,
        pulse_drift=pulse,
        synchrony_index=0.72,
        storylines=("alignment",),
    )
    resonance_layer = GenesisResonanceLayer(_StaticField(report), privacy_layer=privacy)

    observer = ObserverSubsystem()
    observer.record("pulse", {"state": "ok"})
    memory = MemoryUnifier(executions=[])
    intents = IntentResolver(
        [
            NegotiationIntent(
                topic="stability",
                summary="ensure",
                tags=["pulse"],
                desired_outcome="steady",
                priority="high",
            )
        ]
    )
    self_model = SelfModel(observer, memory, intents, privacy_layer=privacy)

    macro = EchoMacroLayer(coordinator, resonance_layer, self_model, privacy_layer=privacy)
    claim = ProofClaim.event_commitment(
        claim_id="event",
        subject="orchestrator",
        event_hash="hash-1",
        payload_secret="payload",
    )
    snapshot = macro.orchestrate(proof_claim=claim, circuit="event_commitment")

    assert snapshot.latest_proof is not None
    assert snapshot.privacy["commitments"]
    assert snapshot.macro_index > 0
    assert snapshot.genesis_state["coordination_index"] > 0
