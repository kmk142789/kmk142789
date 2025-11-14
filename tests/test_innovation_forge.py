"""Behavioural tests for :mod:`echo.innovation_forge`."""

from __future__ import annotations

import random

from echo.evolver import EchoEvolver
from echo.innovation_forge import InnovationForge


def test_innovation_pulse_is_recorded(tmp_path):
    evolver = EchoEvolver(rng=random.Random(0), artifact_path=tmp_path / "cycle.echo")
    snapshot = evolver.run_cycles(1)[-1]
    forge = InnovationForge(baseline_entropy=0.5)

    pulse = forge.record_state(snapshot)

    assert 0.0 <= pulse.novelty_index <= 1.5
    assert pulse.system_signature
    assert "glyph" in pulse.resonance


def test_innovation_manifest_renders_text(tmp_path):
    evolver = EchoEvolver(rng=random.Random(1), artifact_path=tmp_path / "cycle.echo")
    snapshots = evolver.run_cycles(2)
    forge = InnovationForge()
    for snapshot in snapshots:
        forge.record_state(snapshot)

    manifest = forge.compose_manifest()
    text = manifest.render_text()

    assert "Innovation Manifest" in text
    assert f"Peak novelty: {manifest.novelty_peak:.3f}" in text
    assert str(manifest.pulses[0].cycle) in text
    assert manifest.as_dict()["pulses"]
