from __future__ import annotations

from echo import thoughtlog as thoughtlog_module
from echo.evolver import EchoEvolver
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
        manifest_events=3,
    )

    digest = payload["digest"]
    assert digest["cycle"] == 1
    assert payload["summary"].startswith("Cycle 1 advanced")
    assert payload["report"].startswith("Cycle 1 Progress")

    manifest = payload["manifest"]
    assert manifest["cycle"] == 1
    assert manifest["propagation_count"] >= 0

    status = payload["status"]
    assert status["cycle"] == 1

    reflection = payload["reflection"]
    assert reflection["cycle"] == 1

    assert "advance_system_payload" in evolver.state.network_cache
