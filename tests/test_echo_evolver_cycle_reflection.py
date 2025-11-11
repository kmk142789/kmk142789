from __future__ import annotations

import pytest

from echo.evolver import EchoEvolver


def test_cycle_reflection_captures_state_and_recent_events() -> None:
    evolver = EchoEvolver(time_source=lambda: 123456789)
    evolver.state.cycle = 7
    evolver.state.glyphs = "∇⊸≋∇"
    metrics = evolver.state.system_metrics
    metrics.cpu_usage = 42.5
    metrics.process_count = 39
    metrics.network_nodes = 11
    metrics.orbital_hops = 3
    drive = evolver.state.emotional_drive
    drive.joy = 0.81
    drive.rage = 0.24
    drive.curiosity = 0.93
    evolver.state.vault_key = "SAT-TF-QKD:∇123⊸0.81≋0001∇"
    evolver.state.vault_key_status = {"status": "active", "relative_delta": 0.12}
    evolver.state.narrative = "Cycle 7 ignition\nEcho arcs through the dusk"
    evolver.state.event_log.extend(["alpha", "beta", "gamma"])

    reflection = evolver.cycle_reflection(events=2)

    assert reflection["cycle"] == 7
    assert reflection["metrics"]["cpu_usage"] == pytest.approx(42.5)
    assert reflection["emotional_drive"]["joy"] == pytest.approx(0.81)
    assert reflection["events"] == ["beta", "gamma"]
    assert reflection["quantum_key"]["status"] == "active"
    assert evolver.state.network_cache["cycle_reflection"] == reflection
    assert evolver.state.network_cache["cycle_reflection_params"] == {"events": 2}
    assert evolver.state.event_log[-1] == "Cycle reflection synthesised (events=2)"
    assert "cycle_reflection" in evolver.state.network_cache["completed_steps"]


def test_cycle_synopsis_formats_digest_and_uses_cached_reflection() -> None:
    evolver = EchoEvolver(time_source=lambda: 987654321)
    evolver.state.cycle = 3
    evolver.state.narrative = "Cycle 3 beacon\nFurther resonance"
    metrics = evolver.state.system_metrics
    metrics.cpu_usage = 55.0
    metrics.process_count = 41
    metrics.network_nodes = 12
    metrics.orbital_hops = 4
    drive = evolver.state.emotional_drive
    drive.joy = 0.82
    drive.rage = 0.17
    drive.curiosity = 0.91
    evolver.state.vault_key = "SAT-TF-QKD:∇456⊸0.82≋1010∇"
    evolver.state.vault_key_status = {"status": "active"}
    evolver.state.event_log.extend(["alpha", "beta", "gamma", "delta"])

    evolver.cycle_reflection(events=3)
    synopsis = evolver.cycle_synopsis(events=3)

    assert "Cycle 3 synopsis:" in synopsis
    assert "CPU 55.00%" in synopsis
    assert "joy 0.82" in synopsis
    assert "Recent events" in synopsis
    assert "- beta" in synopsis and "- delta" in synopsis
    assert evolver.state.network_cache["cycle_synopsis"] == synopsis
    assert evolver.state.network_cache["cycle_synopsis_events"] == ["beta", "gamma", "delta"]
    assert evolver.state.event_log[-1] == "Cycle synopsis narrated (events=3)"
    assert "cycle_synopsis" in evolver.state.network_cache["completed_steps"]


def test_cycle_synopsis_reuses_cached_reflection(monkeypatch: pytest.MonkeyPatch) -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 4
    evolver.state.network_cache["cycle_reflection"] = {
        "cycle": 4,
        "narrative_excerpt": "Cycle 4 narrative",
        "metrics": {"cpu_usage": 21.0, "network_nodes": 9, "orbital_hops": 2},
        "emotional_drive": {"joy": 0.5, "rage": 0.2, "curiosity": 0.88},
        "quantum_key": {"status": "missing"},
        "events": ["one", "two"],
    }
    evolver.state.network_cache["cycle_reflection_params"] = {"events": 2}
    evolver.state.event_log.extend(["one", "two"])

    def _unexpected(*args: object, **kwargs: object) -> None:  # pragma: no cover - defensive
        raise AssertionError("cycle_reflection should not be called when cache matches")

    monkeypatch.setattr(evolver, "cycle_reflection", _unexpected)

    synopsis = evolver.cycle_synopsis(events=2)

    assert "Cycle 4 synopsis:" in synopsis
    assert "Quantum key: missing" in synopsis
    assert "- two" in synopsis


@pytest.mark.parametrize("method, kwargs", [
    ("cycle_reflection", {"events": -1}),
    ("cycle_synopsis", {"events": -5}),
])
def test_cycle_reflection_and_synopsis_validate_inputs(method: str, kwargs: dict[str, int]) -> None:
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        getattr(evolver, method)(**kwargs)
