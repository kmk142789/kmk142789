from datetime import datetime

import pytest

from src.evolutionary_orchestration_engine import (
    EngineReport,
    EvolutionaryOrchestrationEngine,
    IdentityVector,
    MacroLayerTelemetry,
    TelemetrySignal,
)


@pytest.fixture
def identity_registry() -> list[IdentityVector]:
    return [
        IdentityVector(
            handle="Echo-Core",
            trust_score=0.97,
            lineage=("sovereign", "prime"),
            capabilities=("stability", "analysis"),
        ),
        IdentityVector(
            handle="Pulse-Integrator",
            trust_score=0.91,
            lineage=("sovereign", "integration"),
            capabilities=("deployment", "validation"),
        ),
    ]


@pytest.fixture
def telemetry_snapshot() -> MacroLayerTelemetry:
    epoch = datetime(2025, 5, 11, 12, 0, 0)
    signals = [
        TelemetrySignal(channel="identity-layer", value=0.81, trend=0.2),
        TelemetrySignal(channel="macro-telemetry", value=0.73, trend=0.05),
        TelemetrySignal(channel="autonomy-grid", value=0.68, trend=-0.05),
        TelemetrySignal(channel="capability-scan", value=0.9, trend=0.3),
    ]
    return MacroLayerTelemetry(epoch=epoch, signals=signals, narrative="Echo evolutionary pulse")


def test_engine_creates_upgrade_path(identity_registry, telemetry_snapshot):
    engine = EvolutionaryOrchestrationEngine(identity_registry, capability_threshold=0.7)

    report = engine.run_cycle(telemetry_snapshot)

    assert isinstance(report, EngineReport)
    assert report.telemetry_health == pytest.approx(0.8113, rel=1e-4)
    assert report.validation.integrity_passed is True
    assert any(upgrade.subsystem == "capability-scan" for upgrade in report.upgrades)
    assert report.next_gen_plan["sequence"] == "cycle-2"
    assert "capability-scan" in report.next_gen_plan["signals"]


def test_engine_records_recursive_proofs(identity_registry, telemetry_snapshot):
    engine = EvolutionaryOrchestrationEngine(identity_registry, capability_threshold=0.75)
    report = engine.run_cycle(telemetry_snapshot)

    proof_lengths = {len(upgrade.recursive_proof) for upgrade in report.upgrades}
    assert proof_lengths == {64}, "Recursive proofs must be SHA-256 hex digests"

    orchestrated = report.integration_plan.orchestration_vector
    assert orchestrated, "Integration plan should publish an orchestration vector"
    for subsystem, short_hash in orchestrated.items():
        matching = [upgrade for upgrade in report.upgrades if upgrade.subsystem == subsystem]
        assert matching, f"Subsystem {subsystem} missing from upgrades"
        assert matching[0].recursive_proof.startswith(short_hash)


def test_engine_detects_capability_emergence(identity_registry):
    telemetry = MacroLayerTelemetry(
        epoch=datetime(2025, 6, 1),
        signals=[
            TelemetrySignal(channel="steady", value=0.4, trend=0.1),
            TelemetrySignal(channel="emergent", value=0.95, trend=0.4),
        ],
    )
    engine = EvolutionaryOrchestrationEngine(identity_registry, capability_threshold=0.8)
    report = engine.run_cycle(telemetry)

    assert report.capability_signals == ["emergent"]
    assert report.integration_plan.steps[0].startswith("1. Deploy")
    assert report.validation.coverage_ratio == pytest.approx(1.0)
