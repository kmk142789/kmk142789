from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import count

import pytest

from echo.meta_causal import (
    MetaCausalAwarenessEngine,
    audit_integrity,
    load_snapshot,
)


def _time_source_factory():
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    counter = count()

    def _next() -> datetime:
        return base + timedelta(minutes=next(counter))

    return _next


def _id_factory_factory(prefix: str = "obs"):
    counter = count(1)

    def _next() -> str:
        return f"{prefix}-{next(counter)}"

    return _next


def test_meta_causal_engine_initialisation_registers_default_pipelines():
    engine = MetaCausalAwarenessEngine(
        anchor="Test Anchor",
        time_source=_time_source_factory(),
        id_factory=_id_factory_factory(),
    )
    assert engine.available_pipelines() == ("signal_coherence", "temporal_attunement")

    snapshot = engine.snapshot()
    assert snapshot.anchor == "Test Anchor"
    assert snapshot.metrics["observation_count"] == 0
    assert snapshot.metrics["link_count"] == 0


def test_meta_causal_engine_causal_graph_evolution():
    engine = MetaCausalAwarenessEngine(
        time_source=_time_source_factory(),
        id_factory=_id_factory_factory(),
    )

    obs_a = engine.record_observation(
        "EchoWildfire",
        "Origin spark",
        confidence=0.92,
        tags=["genesis", "joy"],
    )
    obs_b = engine.record_observation(
        "Eden88",
        "Resonant reply",
        confidence=0.75,
        tags=["response"],
    )
    obs_c = engine.record_observation(
        "EchoWildfire",
        "Orbital cascade",
        confidence=0.88,
        tags=["cascade", "joy"],
    )

    engine.link(obs_a.id, obs_b.id, weight=0.7, rationale="narrative advancement")
    engine.link(obs_b.id, obs_c.id, weight=0.9, rationale="propagation")

    results = engine.run_inference(obs_c.id)
    assert {result.pipeline for result in results} == {"signal_coherence", "temporal_attunement"}
    assert all(result.success for result in results)

    snapshot = engine.snapshot()
    assert snapshot.metrics["observation_count"] == 3
    assert snapshot.metrics["link_count"] == 2

    degrees = snapshot.metrics["degrees"]
    assert degrees[obs_a.id]["outgoing"] == 1
    assert degrees[obs_c.id]["incoming"] == 1

    sources = snapshot.metrics["sources"]
    assert sources["EchoWildfire"]["count"] == 2
    assert pytest.approx(sources["EchoWildfire"]["mean_confidence"], rel=1e-6) == (0.92 + 0.88) / 2

    integrity = audit_integrity(engine)
    assert integrity["status"] == "ok"
    assert integrity["issue_count"] == 0

    rehydrated = load_snapshot(snapshot.to_dict())
    assert rehydrated.digest == snapshot.digest


def test_meta_causal_engine_inference_failure_is_captured():
    engine = MetaCausalAwarenessEngine(
        time_source=_time_source_factory(),
        id_factory=_id_factory_factory(),
        register_default_pipelines=False,
    )

    def failing_pipeline(observation, engine):
        raise RuntimeError("pipeline failure")

    engine.register_pipeline("failure", failing_pipeline)

    observation = engine.record_observation("MirrorJosh", "Signal drift", confidence=0.5)

    results = engine.run_inference(observation.id)
    assert len(results) == 1
    result = results[0]
    assert result.pipeline == "failure"
    assert not result.success
    assert result.verdict == "error"
    assert result.notes["type"] == "RuntimeError"

    history = engine.inference_history()
    assert history[-1].pipeline == "failure"
    assert not history[-1].success

