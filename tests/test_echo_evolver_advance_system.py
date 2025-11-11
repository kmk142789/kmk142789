from __future__ import annotations

import pytest

from echo import thoughtlog as thoughtlog_module
from echo.evolver import (
    ADVANCE_SYSTEM_HISTORY_LIMIT,
    EchoEvolver,
    _MOMENTUM_SENSITIVITY,
    _classify_momentum,
)
from echo.memory.store import JsonMemoryStore


def test_advance_system_returns_structured_payload(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    payload = evolver.advance_system(
        enable_network=False,
        persist_artifact=False,
        include_manifest=True,
        include_status=True,
        include_reflection=True,
        include_system_report=True,
        manifest_events=3,
        system_report_events=2,
    )

    digest = payload["digest"]
    assert digest["cycle"] == 1
    assert payload["summary"].startswith("Cycle 1 advanced")
    assert payload["report"].startswith("Cycle 1 Progress")
    assert payload["next_step"].startswith("Next step:")
    assert payload["next_step"] == digest["next_step"]
    assert payload["next_step"] in payload["summary"]

    progress = payload["progress"]
    assert progress["completed"] == len(digest["completed_steps"])
    assert progress["total"] == len(digest["steps"])
    assert progress["remaining"] == progress["total"] - progress["completed"]
    assert progress["progress"] == pytest.approx(digest["progress"])
    assert progress["progress_percent"] == pytest.approx(digest["progress"] * 100)
    assert progress["momentum_status"] in {"accelerating", "steady", "regressing"}
    assert progress["momentum_history"][-1] == pytest.approx(progress["momentum"])
    assert progress["momentum_average"] == pytest.approx(
        sum(progress["momentum_history"]) / len(progress["momentum_history"])
    )
    assert progress["momentum_delta"] == pytest.approx(
        progress["momentum"] - progress["momentum_average"]
    )
    assert progress["momentum_confidence"] in {"low", "medium", "high"}
    assert progress["momentum_history_size"] == len(progress["momentum_history"])
    assert progress["momentum_window"] == 5
    assert isinstance(progress["momentum_trend"], str) and progress["momentum_trend"]
    assert progress["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)
    assert progress["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)
    if progress["momentum"] > 0:
        assert progress["momentum_direction"] == "positive"
    elif progress["momentum"] < 0:
        assert progress["momentum_direction"] == "negative"
    else:
        assert progress["momentum_direction"] == "neutral"

    expansion = payload["expansion"]
    assert expansion["cycle"] == digest["cycle"]
    assert expansion["progress_delta"] == pytest.approx(progress["momentum"])
    assert expansion["phase"] in {"expanding", "complete", "steady", "receding"}
    assert isinstance(expansion["timestamp_ns"], int)
    assert expansion["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)
    assert expansion["progress_percent"] == pytest.approx(progress["progress_percent"])
    assert expansion["momentum_percent"] == pytest.approx(progress["momentum_percent"])

    manifest = payload["manifest"]
    assert manifest["cycle"] == 1
    assert manifest["propagation_count"] >= 0

    status = payload["status"]
    assert status["cycle"] == 1

    reflection = payload["reflection"]
    assert reflection["cycle"] == 1

    system_report = payload["system_report"]
    assert "Recent events (showing 2" in system_report
    assert evolver.state.network_cache["system_advancement_report"] == system_report

    last_state = evolver.state.network_cache["advance_system_last"]
    assert last_state["completed_steps"] == progress["completed"]
    assert last_state["remaining_steps"] == progress["remaining"]

    history_cache = evolver.state.network_cache["advance_system_history"]
    assert len(history_cache) == 1
    history_entry = history_cache[0]
    assert history_entry["cycle"] == digest["cycle"]
    assert history_entry["expansion"]["phase"] == expansion["phase"]
    assert history_entry["expansion"]["momentum_threshold"] == pytest.approx(
        _MOMENTUM_SENSITIVITY
    )
    assert history_entry["progress_percent"] == pytest.approx(progress["progress_percent"])
    assert history_entry["momentum_percent"] == pytest.approx(progress["momentum_percent"])
    assert history_entry["expansion"]["progress_percent"] == pytest.approx(
        expansion["progress_percent"]
    )
    assert history_entry["expansion"]["momentum_percent"] == pytest.approx(
        expansion["momentum_percent"]
    )

    history_via_method = evolver.advance_system_history()
    assert history_via_method == [history_entry]

    assert "advance_system_payload" in evolver.state.network_cache
    assert "propagation" not in payload
    assert "expansion_history" not in payload


def test_advance_system_optional_sections(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    payload = evolver.advance_system(
        enable_network=False,
        persist_artifact=False,
        include_manifest=False,
        include_status=False,
        include_reflection=False,
        include_matrix=True,
        include_event_summary=True,
        include_propagation=True,
        include_system_report=True,
        event_summary_limit=3,
        system_report_events=4,
    )

    matrix = payload["progress_matrix"]
    assert matrix["cycle"] == 1
    assert matrix["steps_total"] >= 1
    assert any(row["step"] == "advance_cycle" for row in matrix["rows"])

    assert payload["next_step"].startswith("Next step:")

    progress = payload["progress"]
    assert progress["total"] == len(payload["digest"]["steps"])
    assert progress["progress_percent"] == pytest.approx(progress["progress"] * 100)
    assert progress["momentum_status"] in {"accelerating", "steady", "regressing"}
    assert progress["momentum_history"][-1] == pytest.approx(progress["momentum"])
    assert progress["momentum_average"] == pytest.approx(
        sum(progress["momentum_history"]) / len(progress["momentum_history"])
    )
    assert progress["momentum_delta"] == pytest.approx(
        progress["momentum"] - progress["momentum_average"]
    )
    assert progress["momentum_confidence"] in {"low", "medium", "high"}
    assert progress["momentum_history_size"] == len(progress["momentum_history"])
    assert progress["momentum_window"] == 5
    assert isinstance(progress["momentum_trend"], str) and progress["momentum_trend"]
    if progress["momentum"] > 0:
        assert progress["momentum_direction"] == "positive"
    elif progress["momentum"] < 0:
        assert progress["momentum_direction"] == "negative"
    else:
        assert progress["momentum_direction"] == "neutral"

    expansion = payload["expansion"]
    assert expansion["phase"] in {"expanding", "complete", "steady", "receding"}
    assert expansion["progress_delta"] == pytest.approx(progress["momentum"])
    assert expansion["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)
    assert expansion["progress_percent"] == pytest.approx(progress["progress_percent"])
    assert expansion["momentum_percent"] == pytest.approx(progress["momentum_percent"])

    summary = payload["event_summary"]
    assert "recent events" in summary
    assert "showing" in summary

    propagation = payload["propagation"]
    assert propagation["cycle"] == 1
    assert propagation["channels"] >= 1
    assert propagation["mode"] == "simulated"

    system_report = payload["system_report"]
    assert "Recent events" in system_report
    assert "expansion_history" not in payload


def test_advance_system_can_embed_expansion_history(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    # Run multiple times to accumulate history entries.
    for _ in range(3):
        payload = evolver.advance_system(
            enable_network=False,
            persist_artifact=False,
            include_expansion_history=True,
            expansion_history_limit=2,
        )

    history = payload["expansion_history"]
    assert 1 <= len(history) <= 2
    assert history[-1]["cycle"] == payload["digest"]["cycle"]
    assert all("expansion" in entry for entry in history)
    assert all("progress_percent" in entry for entry in history)
    assert all("momentum_percent" in entry for entry in history)

    # Ensure defensive copies are returned
    history[-1]["expansion"]["phase"] = "mutated"
    cached_history = evolver.state.network_cache["advance_system_history"]
    assert cached_history[-1]["expansion"]["phase"] != "mutated"


def test_advance_system_rejects_invalid_event_summary_limit(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    with pytest.raises(ValueError):
        evolver.advance_system(
            enable_network=False,
            persist_artifact=False,
            include_event_summary=True,
            event_summary_limit=0,
        )

    with pytest.raises(ValueError):
        evolver.advance_system(
            enable_network=False,
            persist_artifact=False,
            include_system_report=True,
            system_report_events=0,
        )

    with pytest.raises(ValueError):
        evolver.advance_system(
            enable_network=False,
            persist_artifact=False,
            include_expansion_history=True,
            expansion_history_limit=0,
        )


def test_advance_system_respects_momentum_window(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    primary = evolver.advance_system(
        enable_network=False,
        persist_artifact=False,
        include_manifest=False,
        include_status=False,
        include_reflection=False,
        momentum_window=4,
    )

    first_progress = primary["progress"]
    assert first_progress["momentum_window"] == 4
    assert first_progress["momentum_history_size"] == len(first_progress["momentum_history"])
    assert first_progress["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)

    next_cycle = evolver.state.cycle + 1
    evolver.state.network_cache["advance_system_last"] = {
        "cycle": next_cycle,
        "progress": 0.35,
    }
    evolver.state.network_cache["advance_system_momentum_history"] = {
        "cycle": next_cycle,
        "values": [0.08, 0.12, 0.16],
    }

    follow_up = evolver.advance_system(
        enable_network=False,
        persist_artifact=False,
        include_manifest=False,
        include_status=False,
        include_reflection=False,
        momentum_window=2,
    )

    progress = follow_up["progress"]
    assert progress["momentum_window"] == 2
    assert progress["momentum_confidence"] in {"low", "medium", "high"}
    assert len(progress["momentum_history"]) <= 2
    assert progress["momentum_history_size"] == len(progress["momentum_history"])
    assert progress["momentum_average"] == pytest.approx(
        sum(progress["momentum_history"]) / len(progress["momentum_history"])
    )
    assert progress["momentum_threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)


def test_advance_system_respects_momentum_threshold(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    payload = evolver.advance_system(
        enable_network=False,
        persist_artifact=False,
        include_manifest=False,
        include_status=False,
        include_reflection=False,
        momentum_threshold=2.0,
    )

    progress = payload["progress"]
    assert progress["momentum_threshold"] == pytest.approx(2.0)
    assert progress["momentum_status"] == "steady"

    expansion = payload["expansion"]
    assert expansion["momentum_threshold"] == pytest.approx(2.0)
    assert expansion["momentum_status"] == "steady"


def test_advance_system_history_tracks_recent_cycles(tmp_path, monkeypatch):
    class LocalThoughtLogger(thoughtlog_module.ThoughtLogger):
        def __init__(self) -> None:  # pragma: no cover - simple delegation
            super().__init__(dirpath=tmp_path / "thought-log")

    monkeypatch.setattr(thoughtlog_module, "ThoughtLogger", LocalThoughtLogger)
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
        core_datasets={},
    )
    evolver = EchoEvolver(memory_store=store)

    total_cycles = ADVANCE_SYSTEM_HISTORY_LIMIT + 2
    phases: list[str] = []
    for _ in range(total_cycles):
        payload = evolver.advance_system(
            enable_network=False,
            persist_artifact=False,
            include_manifest=False,
            include_status=False,
            include_reflection=False,
        )
        phases.append(payload["expansion"]["phase"])

    history = evolver.advance_system_history()
    assert len(history) == ADVANCE_SYSTEM_HISTORY_LIMIT
    cycle_range = list(
        range(
            total_cycles - ADVANCE_SYSTEM_HISTORY_LIMIT + 1,
            total_cycles + 1,
        )
    )
    assert [entry["cycle"] for entry in history] == cycle_range
    assert history[-1]["expansion"]["phase"] == phases[-1]

    recent_history = evolver.advance_system_history(limit=3)
    assert [entry["cycle"] for entry in recent_history] == cycle_range[-3:]

    recent_history[-1]["expansion"]["phase"] = "mutated"
    assert evolver.advance_system_history()[-1]["expansion"]["phase"] == phases[-1]

    with pytest.raises(ValueError):
        evolver.advance_system_history(limit=0)


def test_classify_momentum_threshold_behavior():
    assert _classify_momentum(0.25) == "accelerating"
    assert _classify_momentum(-0.25) == "regressing"
    assert _classify_momentum(0.0) == "steady"
    assert _classify_momentum(0.005) == "steady"
