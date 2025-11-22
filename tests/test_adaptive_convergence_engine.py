from datetime import datetime, timedelta

from src.adaptive_convergence_engine import (
    AdaptiveConvergenceEngine,
    IdentitySignature,
    SubsystemDescriptor,
    TelemetryFrame,
    TelemetryMetric,
)


def _build_engine() -> AdaptiveConvergenceEngine:
    identities = [
        IdentitySignature(
            handle="atlas",
            baseline_vector={"sync": 0.8, "trust": 0.9},
            current_vector={"sync": 0.7, "trust": 0.95},
            autonomy_layer="core",
            trust=0.92,
        ),
        IdentitySignature(
            handle="helix",
            baseline_vector={"sync": 0.45, "trust": 0.5},
            current_vector={"sync": 0.9, "trust": 0.7},
            autonomy_layer="edge",
            trust=0.88,
        ),
    ]
    subsystems = [
        SubsystemDescriptor(
            name="upgrade-alpha",
            layer="core",
            criticality=0.82,
            load_factor=0.5,
            upgrade_paths=("patch", "rebuild"),
            baseline_version="1.2.0",
        ),
        SubsystemDescriptor(
            name="upgrade-beta",
            layer="edge",
            criticality=0.6,
            load_factor=0.4,
            upgrade_paths=("reindex",),
            baseline_version="2.0.0",
        ),
        SubsystemDescriptor(
            name="upgrade-gamma",
            layer="orbital",
            criticality=0.4,
            load_factor=0.7,
            upgrade_paths=("stabilize",),
            baseline_version="0.9.1",
        ),
    ]
    return AdaptiveConvergenceEngine(identities=identities, subsystems=subsystems, recursion_window=3)


def _build_frames(start: datetime) -> list[TelemetryFrame]:
    return [
        TelemetryFrame(
            epoch=start,
            source="sensor-a",
            metrics=[
                TelemetryMetric("upgrade-alpha", 0.9, weight=1.0, layer="core"),
                TelemetryMetric("upgrade-beta", 0.3, weight=1.0, layer="edge"),
            ],
        ),
        TelemetryFrame(
            epoch=start + timedelta(minutes=5),
            source="sensor-b",
            metrics=[
                TelemetryMetric("upgrade-alpha", 0.8, weight=0.5, layer="core"),
                TelemetryMetric("upgrade-gamma", 0.6, weight=1.5, layer="orbital"),
            ],
        ),
    ]


def test_engine_unifies_telemetry_and_assigns_upgrades() -> None:
    engine = _build_engine()
    frames = _build_frames(datetime(2025, 1, 1, 12, 0, 0))

    report = engine.run_cycle(frames)

    assert report.unified_telemetry.score == 0.625
    assert report.unified_telemetry.channels["upgrade-alpha"] == 0.8667
    assert report.unified_telemetry.anomalies == ["upgrade-beta"]

    resolutions = {res.handle: res for res in report.identity_resolutions}
    assert resolutions["atlas"].verdict == "aligned"
    assert resolutions["helix"].verdict == "stabilize"

    queue = list(report.upgrade_queue)
    assert queue[0].subsystem == "upgrade-alpha"
    assert queue[0].priority == 1
    assert queue[0].owner == "atlas"
    assert queue[1].subsystem == "upgrade-beta"
    assert queue[2].layer == "orbital"

    coherence = {env.layer: env for env in report.layer_coherence}
    assert coherence["core"].identities == ["atlas"]
    assert "upgrade-alpha" in coherence["core"].upgrade_focus

    advisory = report.advisories[0]
    assert advisory.layer == "edge"
    assert advisory.severity == "warning"
    assert "upgrade-beta" in advisory.message


def test_recursive_state_accumulates_history() -> None:
    engine = _build_engine()
    base = datetime(2025, 2, 1, 9, 0, 0)
    report_a = engine.run_cycle(_build_frames(base))
    report_b = engine.run_cycle(_build_frames(base + timedelta(hours=1)))

    assert report_a.recursive_state.depth == 1
    assert report_a.recursive_state.volatility == 0.0

    assert report_b.recursive_state.depth == 2
    assert report_b.recursive_state.history == (0.625, 0.625)
    assert report_b.recursive_state.status == "stable"
