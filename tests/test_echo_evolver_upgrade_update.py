from __future__ import annotations

from typing import Any, Dict

from echo.evolver import EchoEvolver


def _build_payload(sections: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "digest": {"cycle": 1, "progress": 0.5, "steps": []},
        "progress": {"progress": 0.5},
        "summary": "Cycle 1 advanced",
        "report": "Cycle report",
        "metadata": {"source": "test"},
    }
    payload.update(sections)
    return payload


def test_upgrade_system_enables_full_sections(monkeypatch):
    evolver = EchoEvolver()
    captured: Dict[str, Any] = {}

    def fake_advance_system(**kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return _build_payload(
            {
                "manifest": {"cycle": 1},
                "status": {"cycle": 1},
                "reflection": "notes",
                "progress_matrix": {"rows": []},
                "event_summary": "events",
                "propagation": {"mode": "simulated"},
                "system_report": "Recent events",
                "diagnostics": {"cycle": 1},
                "momentum_resonance": {"glyphs": []},
                "momentum_history": {"values": [0.1]},
                "expansion_history": [{"cycle": 1}],
            }
        )

    monkeypatch.setattr(evolver, "advance_system", fake_advance_system)

    payload = evolver.upgrade_system(expansion_history_limit=4, momentum_window=7)

    assert captured["include_manifest"] is True
    assert captured["include_status"] is True
    assert captured["include_reflection"] is True
    assert captured["include_matrix"] is True
    assert captured["include_event_summary"] is True
    assert captured["include_propagation"] is True
    assert captured["include_system_report"] is True
    assert captured["include_diagnostics"] is True
    assert captured["include_momentum_resonance"] is True
    assert captured["include_momentum_history"] is True
    assert captured["include_expansion_history"] is True
    assert captured["expansion_history_limit"] == 4
    assert captured["momentum_window"] == 7

    metadata = payload["metadata"]
    assert metadata["source"] == "test"
    assert metadata["mode"] == "upgrade"
    assert "upgrade_sections" in metadata
    assert "manifest" in metadata["upgrade_sections"]
    assert "momentum_history" in metadata["upgrade_sections"]


def test_upgrade_system_respects_overrides(monkeypatch):
    evolver = EchoEvolver()
    captured: Dict[str, Any] = {}

    def fake_advance_system(**kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return _build_payload({})

    monkeypatch.setattr(evolver, "advance_system", fake_advance_system)

    evolver.upgrade_system(include_propagation=False, include_diagnostics=False)

    assert captured["include_propagation"] is False
    assert captured["include_diagnostics"] is False


def test_update_system_defaults_to_lightweight_payload(monkeypatch):
    evolver = EchoEvolver()
    captured: Dict[str, Any] = {}

    def fake_advance_system(**kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return _build_payload({"status": {"cycle": 1}, "diagnostics": {"cycle": 1}})

    monkeypatch.setattr(evolver, "advance_system", fake_advance_system)

    payload = evolver.update_system()

    assert captured["include_manifest"] is False
    assert captured["include_status"] is True
    assert captured["include_reflection"] is False
    assert captured["include_event_summary"] is False
    assert captured["include_system_report"] is False
    assert captured["include_diagnostics"] is True
    assert captured["include_momentum_resonance"] is False
    assert captured["include_momentum_history"] is False
    assert captured["include_expansion_history"] is False
    assert captured["diagnostics_window"] == 3
    assert captured["momentum_window"] == 3

    metadata = payload["metadata"]
    assert metadata["mode"] == "update"
    assert metadata["update_sections"] == ["status", "diagnostics"]
    assert metadata["update_window"] == {"diagnostics_window": 3, "momentum_window": 3}


def test_update_system_overrides(monkeypatch):
    evolver = EchoEvolver()
    captured: Dict[str, Any] = {}

    def fake_advance_system(**kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return _build_payload({})

    monkeypatch.setattr(evolver, "advance_system", fake_advance_system)

    evolver.update_system(include_manifest=True, diagnostics_window=6)

    assert captured["include_manifest"] is True
    assert captured["diagnostics_window"] == 6
