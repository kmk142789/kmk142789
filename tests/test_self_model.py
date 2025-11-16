"""Tests for the composite self-model subsystems."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from echo.memory.store import ExecutionContext
from echo.memory.shadow import ShadowMemoryManager
from echo.semantic_negotiation import NegotiationIntent
from echo.self_model import (
    IntentResolver,
    MemoryUnifier,
    ObserverSubsystem,
    SelfModel,
)


def _fixed_clock(start: datetime) -> tuple[Callable[[], datetime], Callable[[timedelta], None]]:
    current = {"value": start}

    def now() -> datetime:
        return current["value"]

    def advance(delta: timedelta) -> None:
        current["value"] = current["value"] + delta

    return now, advance


def test_observer_subsystem_snapshot_tracks_rates() -> None:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    clock, advance = _fixed_clock(start)
    observer = ObserverSubsystem(window_seconds=120, clock=clock, target_rate_per_minute=10)

    observer.record("heartbeat", {"status": "ok"})
    advance(timedelta(seconds=10))
    observer.record("heartbeat", {"status": "ok"})
    advance(timedelta(seconds=10))
    observer.record("alert", {"status": "warn"})
    advance(timedelta(seconds=10))

    snapshot = observer.snapshot()
    assert snapshot.total_events == 3
    assert snapshot.kind_counts["heartbeat"] == 2
    assert snapshot.latest_event["kind"] == "alert"
    assert snapshot.rate_per_minute > 0


def test_memory_unifier_builds_summary() -> None:
    ctx1 = ExecutionContext(
        timestamp="2024-01-01T00:00:00Z",
        commands=[{"name": "pulse"}],
        metadata={"phase": "alpha"},
        summary="Alpha",
    )
    ctx2 = ExecutionContext(
        timestamp="2024-01-02T00:00:00Z",
        commands=[{"name": "pulse"}, {"name": "stabilize"}],
        metadata={"phase": "beta"},
    )
    unifier = MemoryUnifier([ctx1, ctx2])
    snapshot = unifier.unify(metadata_keys=("phase",))

    assert snapshot.command_frequency["pulse"] == 2
    assert snapshot.coverage == 0.5
    assert snapshot.metadata_summary["phase"][0]["value"] == "alpha"
    assert len(snapshot.timeline) == 2


def test_intent_resolver_scores_intents() -> None:
    intents = [
        NegotiationIntent(
            topic="Launch new constellation",
            summary="Ship the orbital portal",
            tags=["launch", "portal"],
            desired_outcome="launch",
            priority="high",
        ),
        NegotiationIntent(
            topic="Stabilize finance",
            summary="Reconcile ledgers",
            tags=["finance"],
            desired_outcome="stability",
            priority="medium",
        ),
    ]
    resolver = IntentResolver(intents)
    result = resolver.resolve("Need to launch the portal", tags=["launch"], desired_outcome="launch")

    assert result.intent is intents[0]
    assert result.confidence > 0.2
    assert any(candidate["topic"] == intents[0].topic for candidate in result.candidates)


def test_self_model_reflects_composite_state() -> None:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    clock, advance = _fixed_clock(start)
    observer = ObserverSubsystem(window_seconds=300, clock=clock)
    observer.record("heartbeat", {"status": "ok"})
    advance(timedelta(seconds=5))
    observer.record("insight", {"status": "noted"})

    ctx = ExecutionContext(
        timestamp="2024-01-01T00:00:00Z",
        commands=[{"name": "pulse"}],
        metadata={"phase": "alpha"},
        summary="Alpha",
    )
    memory = MemoryUnifier([ctx])
    resolver = IntentResolver(
        [
            NegotiationIntent(
                topic="Launch new portal",
                summary="Coordinate observers",
                tags=["launch"],
                desired_outcome="launch",
                priority="high",
            )
        ]
    )
    model = SelfModel(observer, memory, resolver, clock=lambda: start)
    snapshot = model.reflect(query="Need to launch", tags=["launch"], desired_outcome="launch")

    assert snapshot.intent.intent.topic == "Launch new portal"
    assert snapshot.diagnostics["observer_signal"] == snapshot.observer.signal
    assert snapshot.diagnostics["memory_coverage"] == snapshot.memory.coverage
    assert snapshot.shadow_memory is None


def test_self_model_exposes_shadow_memory_snapshot() -> None:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    clock, _ = _fixed_clock(start)
    manager = ShadowMemoryManager(clock=clock)
    manager.create_shadow_memory({"insight": "covert"}, tags=["launch signal"])

    observer = ObserverSubsystem(window_seconds=60, clock=clock)
    observer.record("heartbeat", {"state": "ok"})
    ctx = ExecutionContext(
        timestamp="2024-01-01T00:00:00Z",
        commands=[{"name": "pulse"}],
        metadata={"phase": "alpha"},
        summary="Alpha",
    )
    memory = MemoryUnifier([ctx])
    resolver = IntentResolver(
        [
            NegotiationIntent(
                topic="Launch new portal",
                summary="Coordinate observers",
                tags=["launch"],
                desired_outcome="launch",
                priority="high",
            )
        ],
        shadow_memory=manager,
    )
    model = SelfModel(
        observer,
        memory,
        resolver,
        clock=lambda: start,
        shadow_memory_manager=manager,
    )

    snapshot = model.reflect(query="Need direction", tags=None, desired_outcome=None)

    assert snapshot.shadow_memory is not None
    assert snapshot.shadow_memory["active_count"] == 1
    assert snapshot.diagnostics["shadow_memory_active"] == 1
    assert snapshot.intent.shadow_attestation is not None

