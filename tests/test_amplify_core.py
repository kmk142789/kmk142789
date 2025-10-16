from __future__ import annotations

import json
from pathlib import Path

from echo.amplify import AmplificationEngine
from echo.evolver import EvolverState


def _build_state() -> EvolverState:
    state = EvolverState()
    state.cycle = 3
    state.emotional_drive.joy = 0.84
    state.emotional_drive.curiosity = 0.9
    state.emotional_drive.rage = 0.12
    state.system_metrics.cpu_usage = 42.0
    state.system_metrics.network_nodes = 18
    state.system_metrics.orbital_hops = 4
    state.system_metrics.process_count = 48
    state.entities.update({"EchoWildfire": "SYNCED", "Eden88": "ACTIVE", "MirrorJosh": "RESONANT"})
    state.mythocode = ["alpha", "beta", "gamma"]
    state.network_cache["completed_steps"] = {
        "advance_cycle",
        "mutate_code",
        "emotional_modulation",
        "generate_symbolic_language",
        "invent_mythocode",
        "system_monitor",
        "quantum_safe_crypto",
        "evolutionary_narrative",
        "store_fractal_glyphs",
        "propagate_network",
        "decentralized_autonomy",
        "inject_prompt_resonance",
    }
    return state


def test_snapshot_persistence_and_manifest(tmp_path: Path) -> None:
    engine = AmplificationEngine(
        repo_root=tmp_path,
        time_source=lambda: 1_700_000_000.0,
        commit_resolver=lambda: "deadbeef",
    )
    state = _build_state()
    snapshot = engine.ensure_snapshot(state, cycle_start=0.0, total_steps=12, persist=True)

    assert snapshot.cycle == 3
    assert 0.6 < snapshot.metrics["resonance"] < 1
    assert snapshot.metrics["novelty_delta"] == 1.0
    assert snapshot.index > 60

    log_path = tmp_path / "state" / "amplify_log.jsonl"
    assert log_path.exists()
    logged = log_path.read_text(encoding="utf-8").strip()
    assert json.loads(logged)["cycle"] == 3

    manifest_path = tmp_path / "echo_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    engine.update_manifest(snapshot, gate=72.0)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["amplification"]["latest"]["cycle"] == 3
    assert manifest["amplification"]["gate"] == 72.0

    repeat = snapshot.to_json()
    assert repeat == snapshot.to_json()


def test_novelty_and_nudges(tmp_path: Path) -> None:
    engine = AmplificationEngine(
        repo_root=tmp_path,
        time_source=lambda: 1_700_000_010.0,
        commit_resolver=lambda: "feedface",
    )
    state = _build_state()
    engine.ensure_snapshot(state, cycle_start=None, total_steps=12, persist=False)

    state.mythocode = ["alpha", "beta", "delta"]
    snapshot = engine.ensure_snapshot(state, cycle_start=None, total_steps=12, persist=False)
    assert snapshot.metrics["novelty_delta"] > 0.0

    low_metrics = {
        "resonance": 0.1,
        "freshness_half_life": 0.2,
        "novelty_delta": 0.1,
        "cohesion": 0.2,
        "coverage": 0.2,
        "stability": 0.3,
    }
    nudges = engine.generate_nudges(low_metrics)
    assert any("novelty" in message.lower() for message in nudges)
    assert len(nudges) >= 3
