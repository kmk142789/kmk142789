"""Tests for the Orbital Resonance Analyzer."""

from __future__ import annotations

import json
from pathlib import Path

from echo.orbital_resonance_analyzer import (
    CycleSnapshot,
    OrbitalResonanceAnalyzer,
    load_payloads_from_artifact,
)
from echo_eye_ai.evolver import EchoEvolver


def _generate_payloads(tmp_path: Path, cycles: int = 4) -> list[dict]:
    evolver = EchoEvolver(storage_path=tmp_path / "cycle.echo")
    return evolver.run_cycles(cycles)


def test_orbital_resonance_summary_contains_metrics(tmp_path: Path) -> None:
    payloads = _generate_payloads(tmp_path, cycles=4)
    analyzer = OrbitalResonanceAnalyzer.from_payloads(payloads)
    summary = analyzer.summary()

    assert summary["cycles_analyzed"] == 4
    assert summary["glyph_entropy"] > 0
    assert summary["resonance_index"] > 0
    assert isinstance(summary["quantam_alignment"], dict)
    assert summary["projection"]["cycle"] == payloads[-1]["cycle"] + 1


def test_cycle_snapshot_handles_missing_fields() -> None:
    payload = {
        "cycle": 1,
        "glyphs": "∇⊸",
        "emotional_drive": {"joy": 0.9},
        "system_metrics": {},
    }
    snapshot = CycleSnapshot.from_payload(payload)
    assert snapshot.cycle == 1
    assert snapshot.glyph_count == 2
    assert snapshot.joy == 0.9
    assert snapshot.entanglement == 0.0


def test_load_payloads_from_artifact_accepts_list(tmp_path: Path) -> None:
    payloads = _generate_payloads(tmp_path, cycles=2)
    artifact = tmp_path / "payloads.json"
    artifact.write_text(json.dumps(payloads), encoding="utf-8")

    loaded = load_payloads_from_artifact(artifact)
    analyzer = OrbitalResonanceAnalyzer.from_payloads(loaded)
    summary = analyzer.summary()

    assert summary["cycles_analyzed"] == 2
    assert summary["stability_band"] in {"orbital-high", "orbital-stable", "orbital-fragile"}

