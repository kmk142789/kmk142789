from __future__ import annotations

import pytest

from echo import thoughtlog as thoughtlog_module
from echo.evolver import EchoEvolver, _classify_momentum
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
    if progress["momentum"] > 0:
        assert progress["momentum_direction"] == "positive"
    elif progress["momentum"] < 0:
        assert progress["momentum_direction"] == "negative"
    else:
        assert progress["momentum_direction"] == "neutral"

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

    assert "advance_system_payload" in evolver.state.network_cache
    assert "propagation" not in payload


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
    if progress["momentum"] > 0:
        assert progress["momentum_direction"] == "positive"
    elif progress["momentum"] < 0:
        assert progress["momentum_direction"] == "negative"
    else:
        assert progress["momentum_direction"] == "neutral"

    summary = payload["event_summary"]
    assert "recent events" in summary
    assert "showing" in summary

    propagation = payload["propagation"]
    assert propagation["cycle"] == 1
    assert propagation["channels"] >= 1
    assert propagation["mode"] == "simulated"

    system_report = payload["system_report"]
    assert "Recent events" in system_report


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


def test_classify_momentum_threshold_behavior():
    assert _classify_momentum(0.25) == "accelerating"
    assert _classify_momentum(-0.25) == "regressing"
    assert _classify_momentum(0.0) == "steady"
    assert _classify_momentum(0.005) == "steady"
