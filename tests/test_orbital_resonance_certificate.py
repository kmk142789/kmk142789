"""Tests for the orbital resonance certificate in :mod:`echo.evolver`."""

import pytest

from echo.evolver import EchoEvolver, OrbitalResonanceCertificate


def test_orbital_resonance_certificate_forges_signature(tmp_path):
    evolver = EchoEvolver(time_source=lambda: 123456789, artifact_path=tmp_path / "cycle.echo")
    evolver.state.cycle = 3
    evolver.state.glyphs = "∇⊸≋∇∇"

    metrics = evolver.state.system_metrics
    metrics.cpu_usage = 42.0
    metrics.network_nodes = 9
    metrics.process_count = 18
    metrics.orbital_hops = 4

    drive = evolver.state.emotional_drive
    drive.joy = 0.84
    drive.curiosity = 0.91

    ledger = evolver.state.propagation_ledger
    ledger.record_wave(
        events=("alpha", "beta"),
        mode="orbital",
        cycle=3,
        summary="test wave",
        timestamp_ns=123456789,
    )

    certificate = evolver.orbital_resonance_certificate(momentum_window=3)

    assert isinstance(certificate, OrbitalResonanceCertificate)
    payload = certificate.as_dict()

    assert payload["cycle"] == 3
    assert payload["ledger"]["verified"] is True
    assert payload["ledger"]["tip_hash"] == certificate.ledger_tip
    assert payload["resonance_band"]
    assert len(certificate.signature) == 64

    cached = evolver.state.network_cache["orbital_resonance_certificate"]
    assert cached["signature"] == certificate.signature
    assert "orbital_resonance_certificate" in evolver.state.event_log[-1]


def test_orbital_resonance_certificate_rejects_invalid_windows():
    evolver = EchoEvolver()

    for invalid in (0, -1):
        with pytest.raises(ValueError):
            evolver.orbital_resonance_certificate(momentum_window=invalid)
