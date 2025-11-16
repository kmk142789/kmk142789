from __future__ import annotations

import pytest

from echo.emergent_coherence_field import EmergentCoherenceField
from echo.memory.store import ExecutionContext
from echo.self_model import IntentResolver, MemoryUnifier, ObserverSubsystem, SelfModel
from echo.semantic_negotiation import NegotiationIntent


def _sample_memory_unifier() -> MemoryUnifier:
    contexts = [
        ExecutionContext(
            timestamp="2024-01-01T00:00:00+00:00",
            commands=[{"name": "echo.echoctl", "args": ["cycle"]}],
            metadata={"intent": "alignment", "phase": "cycle"},
            summary="cycle alignment",
        ),
        ExecutionContext(
            timestamp="2024-01-02T00:00:00+00:00",
            commands=[{"name": "echo.echoctl", "args": ["plan"]}],
            metadata={"intent": "alignment", "phase": "plan"},
            summary="plan alignment",
        ),
    ]
    return MemoryUnifier(contexts)


def test_emergent_coherence_field_produces_report() -> None:
    observer = ObserverSubsystem(window_seconds=120, max_events=64)
    for idx in range(6):
        observer.record("continuum", {"lane": "foundation", "idx": idx})

    field = EmergentCoherenceField(observer=observer, memory_unifier=_sample_memory_unifier())
    report = field.evaluate()

    assert report.name == "emergent_coherence_alignment"
    assert report.total_modules > 0
    assert 0.0 <= report.coherence_index <= 1.0
    assert len(report.layer_alignment) >= 1
    payload = report.to_dict()
    assert payload["layer_alignment"], "alignment payload should not be empty"
    assert any(guarantee["name"] == "layer_distribution" for guarantee in payload["guarantees"])


def test_emergent_coherence_field_from_self_model() -> None:
    observer = ObserverSubsystem(window_seconds=60, max_events=32)
    observer.record("pulse", {"kind": "creative"})
    memory_unifier = _sample_memory_unifier()
    intent_resolver = IntentResolver(
        [
            NegotiationIntent(
                topic="coherence",
                summary="bind layers",
                tags=["foundation", "synthesis"],
                desired_outcome="aligned capability",
                priority="p0",
            )
        ]
    )
    self_model = SelfModel(observer, memory_unifier, intent_resolver)
    expected_signal = observer.snapshot().signal

    field = EmergentCoherenceField.from_self_model(self_model)
    report = field.evaluate()

    assert field.observer is observer
    assert set(field.layer_targets).issuperset({"foundation", "synthesis", "expression"})
    assert pytest.approx(report.observer_signal, rel=0, abs=1e-4) == expected_signal
    assert report.memory_coverage >= 0.5
