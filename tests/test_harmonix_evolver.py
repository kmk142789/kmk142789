"""Tests for the functional cognitive Harmonix EchoEvolver implementation."""

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


def test_propagate_network_supports_live_mode() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 2

    events = evolver.propagate_network(enable_network=True)

    assert any("channel engaged" in event for event in events)
    assert any("Live network mode" in entry for entry in evolver.state.events)
    assert evolver.state.network_cache["propagation_events"] == events
