from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from echo.continuum_resonance_field import ContinuumResonanceReport, LaneResonance, PulseDrift
from echo.echo_genesis_core import EchoGenesisCore, SubsystemProbe
from echo.echo_genesis_coordinator import EchoGenesisCoordinator
from echo.echo_macro_layer import EchoMacroLayer
from echo.genesis_resonance_layer import GenesisResonanceLayer
from echo.privacy.zk_layer import (
    CapabilityCircuit,
    EventCommitmentCircuit,
    HashCommitmentBackend,
    KeyOwnershipCircuit,
    ZeroKnowledgePrivacyLayer,
)
from echo.self_model import IntentResolver, MemoryUnifier, ObserverSubsystem, SelfModel
from echo.semantic_negotiation import NegotiationIntent
from echo.sovereign_coordination_kernel import SovereignCoordinationKernel
from echo.sovereign_identity_kernel import CapabilityIdentityKernel, IdentityKernelConfig


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
        probe=lambda: {"signal": 0.82, "health": 0.8},
        weight=1.0,
    )


def _build_macro_layer(tmp_path: Path) -> tuple[EchoMacroLayer, ZeroKnowledgePrivacyLayer]:
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
        extractor=lambda _: {"signal": 0.8, "health": 0.85},
    )
    pulse = PulseDrift(
        total_events=4,
        cadence_seconds=120.0,
        latest_timestamp=None,
        latest_message=None,
        channel_counts={"pulse": 4},
        stability_index=0.78,
    )
    lanes = [
        LaneResonance(
            lane="docs",
            activity_ratio=0.6,
            doc_ratio=0.7,
            code_ratio=0.3,
            freshness_days=1.0,
            resonance_index=0.74,
        )
    ]
    report = ContinuumResonanceReport(
        root=tmp_path,
        generated_at=datetime.now(timezone.utc),
        lanes=lanes,
        pulse_drift=pulse,
        synchrony_index=0.71,
        storylines=("alignment",),
    )
    resonance_layer = GenesisResonanceLayer(_StaticField(report), privacy_layer=privacy)
    observer = ObserverSubsystem()
    observer.record("pulse", {"state": "ok", "signal": 0.9})
    memory = MemoryUnifier(executions=[])
    intents = IntentResolver(
        [
            NegotiationIntent(
                topic="stability",
                summary="protect macro alignment",
                tags=["pulse"],
                desired_outcome="steady",
                priority="high",
            )
        ]
    )
    self_model = SelfModel(observer, memory, intents, privacy_layer=privacy)
    macro_layer = EchoMacroLayer(coordinator, resonance_layer, self_model, privacy_layer=privacy)
    return macro_layer, privacy


def _identity_kernel(tmp_path: Path) -> CapabilityIdentityKernel:
    tmp_path.mkdir(parents=True, exist_ok=True)
    shell_path = tmp_path / "echo_shell.py"
    shell_path.write_text("print('ok')\n", encoding="utf-8")
    config = IdentityKernelConfig(vault_root=tmp_path / "vault", passphrase="pass", shell_path=shell_path)
    return CapabilityIdentityKernel(config)


def test_sovereign_coordination_kernel_unifies_layers(tmp_path: Path) -> None:
    macro_layer, privacy = _build_macro_layer(tmp_path)
    identity_kernel = _identity_kernel(tmp_path / "identity")
    kernel = SovereignCoordinationKernel(identity_kernel, macro_layer, privacy_layer=privacy)

    report = kernel.coordinate(
        subject_did="did:echo:agent:test",
        requested_capabilities=("macro.stabilize",),
        capability_constraints={"scope": "macro", "ttl": 3600},
        policy_context={"lane": "docs"},
        intent_query="stability",
        intent_tags=["pulse"],
        desired_outcome="steady",
    )

    assert report.capability_plan.subject == "did:echo:agent:test"
    assert report.capability_plan.capabilities == ("macro.stabilize",)
    assert report.capability_plan.credential["issuer"] == identity_kernel.issuer_did
    assert len(report.capability_plan.policy_digest) == 64
    assert report.capability_plan.constraints["scope"] == "macro"
    assert report.capability_proof is not None and report.capability_proof["verified"]
    assert report.recursive_proofs["kernel"]["depth"] >= 1
    assert report.recursive_proofs["macro"]["verified"] is True
    assert report.autonomy_directives[0].name == "stability"
    assert report.identity["issuer_did"] == identity_kernel.issuer_did
    assert "proof_pipeline" in report.identity["state"]
    assert isinstance(report.identity["state"], dict)
    assert report.privacy["macro"]["privacy_signal"] >= 0.0
    assert report.privacy["latest_capability_proof"]["claim_id"].startswith("sovereign-cap-")
    assert report.alignment["topic"] == "stability"
