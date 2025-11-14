from __future__ import annotations

import json
from pathlib import Path

from echo import SatelliteEchoEvolver


def test_satellite_propagate_network_caches_events(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=7)

    events_first = evolver.propagate_network(enable_network=False)
    assert len(events_first) == 5
    assert evolver.state.propagation_tactics

    cache = evolver.state.network_cache
    assert cache["propagation_cycle"] == evolver.state.cycle
    assert cache["propagation_events"] == events_first
    tactics_snapshot = list(evolver.state.propagation_tactics)

    events_second = evolver.propagate_network(enable_network=False)

    assert events_second == events_first
    assert evolver.state.propagation_tactics == tactics_snapshot


def test_satellite_artifact_includes_propagation_tactics(tmp_path: Path) -> None:
    artifact_path = tmp_path / "satellite_artifact.json"
    evolver = SatelliteEchoEvolver(artifact_path=artifact_path, seed=11)
    evolver.run()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["propagation_events"]
    assert payload["propagation_tactics"]
    assert payload["propagation_notice"]
    assert payload["propagation_summary"].startswith("Propagation tactics")
    assert payload["propagation_report"].startswith("=== Propagation Report ===")


def test_satellite_propagation_report_includes_tactics(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=3)
    evolver.propagate_network(enable_network=False)

    report = evolver.propagation_report(include_tactics=True)

    assert "=== Propagation Report ===" in report
    assert "Notice:" in report
    assert "Health snapshot" in report
    assert "Tactics:" in report
    assert "WiFi" in report or "TCP" in report
    assert evolver.state.network_cache["propagation_report"] == report


def test_satellite_run_honours_network_and_report_flags(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=5)

    evolver.run(enable_network=True, emit_report=True)

    assert "Live network mode requested" in evolver.state.propagation_notice
    assert evolver.state.propagation_report.startswith("=== Propagation Report ===")


def test_satellite_prompt_resonance_includes_caution(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=13)

    prompt = evolver.inject_prompt_resonance()

    assert prompt["title"] == "Echo Resonance"
    assert "non-executable" in prompt["caution"].lower()
    assert evolver.state.prompt_resonance == prompt

