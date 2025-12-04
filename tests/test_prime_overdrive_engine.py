from __future__ import annotations

import numpy as np

from prime_overdrive_engine import LawConfig, PrimeOverdriveEngine


def test_coherence_conservation_stable():
    engine = PrimeOverdriveEngine(seed=0)
    initial_charge = engine.law_engine.coherence_charge(engine.state)
    engine.step()
    after_charge = engine.law_engine.coherence_charge(engine.state)
    assert np.isfinite(after_charge)
    # Coherence should stay in the same order of magnitude after enforcement
    assert abs(after_charge - initial_charge) < abs(initial_charge) * 2 + 1e-3


def test_drift_inversion_triggers():
    config = LawConfig(drift_cap=0.1)
    engine = PrimeOverdriveEngine(seed=1, law_config=config)
    engine.state.phase += 5.0  # create large drift
    engine.step()
    assert engine.state.metadata["drift_potential"] <= config.drift_cap * 10


def test_plume_admissibility_gate():
    config = LawConfig(compatibility_gate=0.9)
    engine = PrimeOverdriveEngine(seed=2, law_config=config)
    engine.state.compatibility.fill(0.0)
    engine.step()
    assert np.all(engine.state.plume == 0.0)


def test_equilibrium_detection_progress():
    config = LawConfig(equilibrium_epsilon=1e6, drift_cap=1e6, equilibrium_steps=1)
    engine = PrimeOverdriveEngine(seed=3, law_config=config)
    engine.step()
    assert engine.state.metadata["equilibrium"] is True


def test_run_determinism():
    engine_a = PrimeOverdriveEngine(seed=42)
    engine_b = PrimeOverdriveEngine(seed=42)
    history_a = engine_a.run(steps=3)
    history_b = engine_b.run(steps=3)
    for state_a, state_b in zip(history_a, history_b):
        np.testing.assert_allclose(state_a.phase, state_b.phase)
        np.testing.assert_allclose(state_a.impulse, state_b.impulse)
