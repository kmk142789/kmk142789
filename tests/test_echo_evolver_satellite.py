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
    assert payload["propagation_metrics"]["average_quality"] >= 0
    assert payload["propagation_metrics"]["best_channels"]
    assert payload["resilience_score"] >= 0
    assert payload["resilience_grade"]
    assert payload["resilience_summary"]


def test_satellite_propagation_metrics_and_report(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=23)

    events = evolver.propagate_network(enable_network=True)

    metrics = evolver.state.propagation_metrics
    assert events
    assert metrics
    assert metrics["average_quality"] >= 0
    assert metrics["quality_ceiling"] >= metrics["quality_floor"]
    assert metrics["best_channels"]

    report = evolver.propagation_report()
    assert "Quality metrics:" in report
    assert "Average quality" in report
    assert evolver.state.network_cache["propagation_metrics"] == metrics


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


def test_satellite_resilience_report_and_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifact.json"
    evolver = SatelliteEchoEvolver(artifact_path=artifact_path, seed=17)

    evolver.propagate_network()
    result = evolver.evaluate_resilience()
    report = evolver.resilience_report()
    evolver.write_artifact()

    assert 0.0 <= result["score"] <= 1.0
    assert result["grade"] in {"Prime", "Stable", "Watch", "Critical"}
    assert "Resilience score" in report

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["resilience_score"] == evolver.state.resilience_score
    assert payload["resilience_grade"] == evolver.state.resilience_grade
    assert payload["resilience_summary"].startswith("Resilience score")


def test_satellite_resilience_refreshes_when_cycle_changes(tmp_path: Path) -> None:
    evolver = SatelliteEchoEvolver(artifact_path=tmp_path / "artifact.json", seed=19)

    evolver.propagate_network()
    initial_events = list(evolver.state.propagation_events)
    cached_cycle = evolver.state.network_cache["propagation_cycle"]

    evolver.state.cycle = cached_cycle + 1

    result = evolver.evaluate_resilience()

    assert evolver.state.network_cache["propagation_cycle"] == evolver.state.cycle
    assert evolver.state.propagation_events != initial_events
    assert 0.0 <= result["score"] <= 1.0

