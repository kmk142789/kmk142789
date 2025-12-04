import math
from datetime import datetime, timedelta, timezone

from echo.reciprocal_resonance_engine import (
    Commitment,
    ReciprocalResonanceEngine,
    SignalEvent,
)


def build_engine():
    return ReciprocalResonanceEngine(decay_half_life_seconds=600, coherence_floor=0.1)


def test_temporal_decay_favors_recent_events():
    engine = build_engine()
    now = datetime.now(timezone.utc)
    recent = SignalEvent(
        source="observability",
        timestamp=now,
        features={"latency_ms": 100},
        confidence=1.0,
    )
    old = SignalEvent(
        source="observability",
        timestamp=now - timedelta(hours=1),
        features={"latency_ms": 1000},
        confidence=1.0,
    )
    engine.ingest_event(recent)
    engine.ingest_event(old)

    aggregate = engine._aggregate_signals(now)
    assert aggregate["latency_ms"] < 200  # old event decays sharply


def test_bpa_scores_alignment_and_rank_order():
    engine = build_engine()
    now = datetime.now(timezone.utc)
    engine.ingest_event(
        SignalEvent(
            source="metrics",
            timestamp=now,
            features={"error_rate": 0.01, "latency_ms": 110},
            confidence=0.9,
        )
    )
    aligned = Commitment(
        actor="SRE",
        intent="Hold error_rate 1% and latency 100-120ms",
        predicted_features={"error_rate": 0.01, "latency_ms": 115},
        horizon_seconds=1800,
        risk_tolerance=0.4,
        weight=1.1,
    )
    misaligned = Commitment(
        actor="Growth",
        intent="Accept high errors for speed",
        predicted_features={"error_rate": 0.10, "latency_ms": 50},
        horizon_seconds=1800,
        risk_tolerance=0.6,
        weight=1.0,
    )
    engine.register_commitment(aligned)
    engine.register_commitment(misaligned)

    results = engine.evaluate(now=now)
    assert results[0].commitment.actor == "SRE"
    assert results[0].overall_score > results[1].overall_score
    assert results[0].forward_error < results[1].forward_error


def test_influence_graph_emits_nodes_and_edges():
    engine = build_engine()
    now = datetime.now(timezone.utc)
    engine.ingest_event(
        SignalEvent(
            source="policy",
            timestamp=now,
            features={"quota": 0.7},
            confidence=0.8,
        )
    )
    engine.register_commitment(
        Commitment(
            actor="Compliance",
            intent="Maintain quota >= 0.6",
            predicted_features={"quota": 0.6},
            horizon_seconds=1200,
            risk_tolerance=0.5,
            weight=1.0,
        )
    )

    graph = engine.influence_graph(now=now)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert any(n.startswith("commitment:") for n in node_ids)
    assert any(n.startswith("signal:quota") for n in node_ids)
    assert graph["edges"]


def test_handles_missing_overlaps_gracefully():
    engine = build_engine()
    now = datetime.now(timezone.utc)
    engine.ingest_event(
        SignalEvent(
            source="telemetry",
            timestamp=now,
            features={"uptime": 0.999},
            confidence=1.0,
        )
    )
    engine.register_commitment(
        Commitment(
            actor="Security",
            intent="Reduce blast radius",
            predicted_features={"isolation": 1.0},
            horizon_seconds=900,
        )
    )

    results = engine.evaluate(now=now)
    assert results
    assert 0 <= results[0].overall_score <= 1
    # With no overlap, forward_error should max out to 1.0 and recommendations should suggest action.
    assert math.isclose(results[0].forward_error, 1.0)
    assert results[0].recommendations
