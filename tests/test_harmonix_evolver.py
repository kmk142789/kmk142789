"""Tests for the functional cognitive Harmonix EchoEvolver implementation."""

import json
import subprocess
import sys

from cognitive_harmonics.harmonix_evolver import EchoEvolver


def test_run_cycle_payload_matches_schema_keys():
    evolver = EchoEvolver()
    state, payload = evolver.run_cycle()

    assert payload["waveform"] == "complex_harmonic"
    assert payload["compression"] is True
    assert payload["lyricism_mode"] is True
    assert payload["symbolic_inflection"] == "fractal"
    assert payload["emotional_tuning"] == "energizing"

    metadata = payload["metadata"]
    assert metadata["vision_banner"].startswith("[:: Vision Protocol Activated ::]")
    assert "EchoEvolver orbits" in metadata["narrative"]
    assert state.cycle == metadata["cycle"]
    assert state.vault_key == metadata["quantum_key"]
    assert state.prompt_resonance == metadata["prompt_resonance"]
    assert "caution" in metadata["prompt_resonance"]
    assert "executable" in metadata["prompt_resonance"]["caution"]
    assert metadata["storyboard"]
    assert metadata["storyboard"][0].startswith("Frame 1")
    assert metadata["propagation_events"]
    assert metadata["propagation_events"] == state.network_cache["propagation_events"]
    snapshot = metadata["propagation_snapshot"]
    assert snapshot is not None
    assert snapshot["mode"] == "simulated"
    assert snapshot["channels"] == len(metadata["propagation_events"])
    assert snapshot["timeline"] is None
    assert metadata["constellation_map"]["title"].startswith("Orbital Constellation")
    assert metadata["constellation_map"]["pattern"]
    assert all("glyph" in step for step in metadata["constellation_map"]["pattern"])
    assert state.events, "Events should log the harmonix operations"


def test_artifact_text_contains_core_sections():
    evolver = EchoEvolver()
    evolver.run_cycle()
    artifact = evolver.build_artifact()

    assert "EchoEvolver: Nexus Evolution Cycle v4" in artifact
    assert "Quantum Key:" in artifact
    assert "Emotional Drive:" in artifact
    assert "\"caution\":" in artifact or "caution" in artifact
    assert "Storyboard:" in artifact
    assert "Propagation Events:" in artifact
    assert "Constellation Map:" in artifact


def test_propagate_network_supports_live_mode() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 2

    events = evolver.propagate_network(enable_network=True)

    assert any("channel engaged" in event for event in events)
    assert any("Live network mode" in entry for entry in evolver.state.events)
    assert evolver.state.network_cache["propagation_events"] == events


def test_run_cycles_returns_reports() -> None:
    evolver = EchoEvolver()
    reports = evolver.run_cycles(3)

    assert [entry["cycle"] for entry in reports] == [1, 2, 3]
    assert reports[-1]["state"]["cycle"] == 3
    assert reports[-1]["payload"]["metadata"]["cycle"] == 3
    # Ensure snapshots are detached and not mutated by later cycles
    assert reports[0]["state"]["cycle"] == 1


def test_run_cycles_requires_positive_count() -> None:
    evolver = EchoEvolver()

    try:
        evolver.run_cycles(0)
    except ValueError as exc:  # pragma: no cover - short negative path
        assert "at least 1" in str(exc)
    else:  # pragma: no cover - defensive guard if validation regresses
        raise AssertionError("ValueError not raised for non-positive cycle count")


def test_cli_supports_multiple_cycles() -> None:
    cmd = [
        sys.executable,
        "-m",
        "cognitive_harmonics.harmonix_evolver",
        "--cycles",
        "2",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["cycles"][0]["cycle"] == 1
    assert payload["cycles"][1]["cycle"] == 2
    assert payload["final_state"]["cycle"] == 2


def test_cli_can_emit_propagation_timeline() -> None:
    cmd = [
        sys.executable,
        "-m",
        "cognitive_harmonics.harmonix_evolver",
        "--propagation-timeline",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    snapshot = payload["propagation_snapshot"]
    assert snapshot["timeline"]
    assert snapshot["timeline_length"] == len(snapshot["timeline"])
    assert snapshot["mode"] == "simulated"
    assert payload["metadata"]["propagation_snapshot"]["timeline"]
