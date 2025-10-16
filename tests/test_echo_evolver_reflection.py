import random

import pytest

from echo.evolver import EchoEvolver


def test_render_reflection_snapshot_is_isolated() -> None:
    evolver = EchoEvolver(rng=random.Random(0))
    evolver.advance_cycle()
    evolver.mutate_code()

    reflection = evolver.render_reflection(include_events=True)

    assert reflection["cycle"] == evolver.state.cycle
    assert 0 <= reflection["progress"] <= 1
    assert reflection["next_step"].startswith("Next step:")
    assert reflection["emotional_drive"]["joy"] == pytest.approx(
        evolver.state.emotional_drive.joy
    )
    assert reflection["entities"]["Eden88"] == "ACTIVE"

    # The event log returned with the snapshot should not include the reflection entry.
    assert "event_log" in reflection
    assert reflection["event_log"][-1].startswith("Cycle digest computed")
    assert evolver.state.event_log[-1].startswith("Reflection rendered")

    # Mutating the returned snapshot must not leak back into the evolver state.
    reflection["glyphs"] += "✨"
    reflection["entities"]["Eden88"] = "ALTERED"
    assert not evolver.state.glyphs.endswith("✨")
    assert evolver.state.entities["Eden88"] == "ACTIVE"

    cached = evolver.state.network_cache["reflection_snapshot"]
    assert cached is not reflection
    assert cached["entities"]["Eden88"] == "ACTIVE"


def test_render_reflection_excludes_events_by_default() -> None:
    evolver = EchoEvolver(rng=random.Random(1))

    snapshot = evolver.render_reflection()

    assert "event_log" not in snapshot
    assert snapshot["cycle"] == evolver.state.cycle
