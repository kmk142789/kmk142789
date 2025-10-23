"""Tests covering new event log and timeline helpers in :mod:`echo.evolver`."""

from __future__ import annotations

from echo.evolver import EchoEvolver


class FakeClock:
    """Deterministic clock used to control timestamp evolution in tests."""

    def __init__(self, *, start: int = 0, step: int = 100) -> None:
        self.current = start
        self.step = step

    def tick(self) -> int:
        self.current += self.step
        return self.current


def test_event_log_statistics_filters_and_caches_patterns() -> None:
    evolver = EchoEvolver()

    evolver.describe_sequence()
    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.pending_steps()
    evolver.cycle_digest()

    stats = evolver.event_log_statistics(limit=4, include_patterns=["cycle", "mutation", "cycle"])

    assert stats["total_events"] == 5
    assert stats["considered_events"] == 4
    assert stats["matched_events"] == 3
    assert stats["coverage_ratio"] == 0.75
    assert stats["pattern_counts"] == {"cycle": 3, "mutation": 1}
    assert stats["first_event"] == "Cycle 1 initiated"
    assert stats["last_event"].startswith("Cycle digest computed")
    assert stats["recent_events"][-1].startswith("Cycle digest computed")

    cached = evolver.state.network_cache["event_log_statistics"]
    assert cached["matched_events"] == 3
    assert cached["recent_events"][-1].startswith("Cycle digest computed")
    assert "Event log statistics computed" in evolver.state.event_log[-1]


def test_cycle_timeline_orders_history_and_records_cache() -> None:
    clock = FakeClock()
    evolver = EchoEvolver(time_source=clock.tick)

    empty_timeline = evolver.cycle_timeline()
    assert empty_timeline == {
        "cycle": 0,
        "count": 0,
        "first_timestamp_ns": None,
        "last_timestamp_ns": None,
        "steps": [],
    }
    assert "Cycle timeline exported (cycle=0, steps=0)" in evolver.state.event_log[-1]

    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()

    timeline = evolver.cycle_timeline()
    assert timeline["cycle"] == 1
    assert timeline["count"] == 3
    assert [entry["step"] for entry in timeline["steps"]] == [
        "advance_cycle",
        "mutate_code",
        "emotional_modulation",
    ]
    assert timeline["steps"][0]["elapsed_ns"] == 0
    assert timeline["steps"][1]["elapsed_ns"] > 0

    cache = evolver.state.network_cache["cycle_timelines"][1]
    assert cache["count"] == 3
    assert cache["steps"][0]["order"] == 1
    assert "cycle=1" in evolver.state.event_log[-1]
    assert "steps=3" in evolver.state.event_log[-1]

    previous_cycle = evolver.cycle_timeline(cycle=0)
    assert previous_cycle["cycle"] == 0
    assert previous_cycle["count"] == 0
    assert previous_cycle["steps"] == []
