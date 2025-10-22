import math
import random

import pytest

from echo.quantum_synchronizer import QuantumSynchronizer
from echo.resonance import HarmonicsAI


@pytest.fixture()
def seeded_synchronizer() -> QuantumSynchronizer:
    harmonics = HarmonicsAI(rng=random.Random(0))
    return QuantumSynchronizer(harmonics, horizon=4, drift_window=3)


def test_quantum_synchronizer_metrics(seeded_synchronizer: QuantumSynchronizer) -> None:
    sync = seeded_synchronizer
    sync.ingest("alpha", timestamp=1.0)
    sync.ingest("beta", timestamp=2.0)
    sync.ingest("gamma", timestamp=3.0)
    report = sync.synchronize()

    assert len(sync.history()) == 3
    assert report.weighted_score == pytest.approx(51.6, rel=1e-6)
    assert report.resonance_drift == pytest.approx(-0.3, rel=1e-6)
    assert report.stability_index == pytest.approx(0.869565, rel=1e-6)
    assert report.pattern_diversity == pytest.approx(1.0, rel=1e-6)
    assert report.momentum == pytest.approx(-0.15, rel=1e-6)
    assert report.novelty_burst == pytest.approx(1.0, rel=1e-6)


def test_quantum_synchronizer_horizon_rotation(seeded_synchronizer: QuantumSynchronizer) -> None:
    sync = seeded_synchronizer
    for idx, word in enumerate(["alpha", "beta", "gamma", "delta", "epsilon"]):
        sync.ingest(word, timestamp=float(idx))
    history = sync.history()
    assert len(history) == 4
    assert history[0].text == "beta"
    assert history[-1].text == "epsilon"


def test_quantum_manifest_render(seeded_synchronizer: QuantumSynchronizer) -> None:
    sync = seeded_synchronizer
    sync.ingest("alpha", timestamp=1.0)
    manifest = sync.emergent_manifest()
    assert "Quantum Synchronizer Manifest" in manifest
    assert "Signals tracked" in manifest
    assert "Weighted score" in manifest
