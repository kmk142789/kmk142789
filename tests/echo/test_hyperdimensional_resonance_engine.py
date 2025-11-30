from __future__ import annotations

from echo.hyperdimensional_resonance_engine import (
    FeedbackStabilityLayer,
    HyperdimensionalResonanceEngine,
    ResonancePulse,
    SpectralAlignmentLayer,
    StrategicVectorLayer,
)


def _build_engine() -> HyperdimensionalResonanceEngine:
    layers = [
        SpectralAlignmentLayer("spectral", weight=1.0, config={"threshold": 0.0}),
        StrategicVectorLayer("strategic", weight=1.0),
        FeedbackStabilityLayer(
            "feedback",
            config={"momentum_threshold": 0.0, "boost": 1, "penalty": 1, "max_priority": 5},
        ),
    ]
    return HyperdimensionalResonanceEngine(layers, max_feedback_cycles=2)


def test_feedback_layer_carries_state_across_cycles() -> None:
    pulse = ResonancePulse(
        id="pulse-feedback",
        intent="stateful",
        payload={"summary": "Hyperdimensional resonance anchors across cycles."},
        priority=1,
        tags=["init"],
    )

    report = _build_engine().run([pulse])
    first_cycle, second_cycle = report.pulses

    assert first_cycle.payload["feedback"]["trend"] == "steady"
    assert second_cycle.payload["feedback"]["trend"] == "rising"
    assert "momentum-rise" in second_cycle.tags
    assert second_cycle.priority > first_cycle.priority
    assert second_cycle.payload["feedback"]["delta"] > 0


def test_feedback_metrics_are_recorded() -> None:
    pulse = ResonancePulse(
        id="pulse-metrics",
        intent="metrics",
        payload={"summary": "Capture feedback drift across the resonance field."},
    )

    report = _build_engine().run([pulse])

    drift_log = report.metrics["feedback_drift"]
    assert len(drift_log) == 2
    assert {entry["trend"] for entry in drift_log} == {"steady", "rising"}

    last_vectors = report.metrics["last_vectors"]
    assert last_vectors["pulse-metrics"]["momentum"] == report.pulses[-1].payload["vector"]["momentum"]
