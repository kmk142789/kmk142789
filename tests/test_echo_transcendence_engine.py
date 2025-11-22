import math

import pytest

from src.echo_transcendence_engine import (
    EchoTranscendenceEngine,
    HelixInput,
    compose_transcendence_manifest,
    demo,
)


@pytest.fixture()
def sample_inputs():
    return (
        HelixInput(channel="orbits", samples=[0.44, 0.95, 1.2, 0.81], phase_hint=0.36),
        HelixInput(channel="tidal", samples=[1.05, 0.88, 0.71, 0.63], phase_hint=0.68),
        HelixInput(channel="beacon", samples=[1.55, 0.25, 0.95, 0.85], phase_hint=0.42),
    )


def test_signature_is_deterministic(sample_inputs):
    engine = EchoTranscendenceEngine()
    signature = engine.synthesize(
        sample_inputs, horizon="aurora signal", anchor="lattice of first light"
    )

    assert signature.label == "orbital-triad:v1"
    assert signature.triad_vector == pytest.approx(
        (-5.782411586589357e-18, 0.5495790758948654, 0.3673728484654037), rel=1e-9
    )
    assert signature.novelty_score == pytest.approx(1.858552)
    assert math.isclose(signature.coherence, 0.893, rel_tol=1e-6)
    assert set(signature.deviation_map) == {"orbits", "tidal", "beacon"}


def test_compose_manifest_round_trip(sample_inputs):
    manifest = compose_transcendence_manifest(
        horizon="aurora signal", anchor="lattice of first light", inputs=sample_inputs
    )

    assert "World-first stamp: orbital-triad:v1" in manifest
    assert "Triad vector" in manifest
    assert "Deviation map" in manifest


def test_demo_stays_stable():
    output = demo()
    assert "aurora signal" in output
    assert "orbital-triad:v1" in output
