import numpy as np

from echo.cognitive_equilibrium_regulator import CognitiveEquilibriumRegulator
from echo.cognitive_field_inference_engine import CFIEngine


def test_equilibrium_intervention_updates_manifold():
    engine = CFIEngine(rng=np.random.default_rng(0), noise_scale=0.0)
    cer = CognitiveEquilibriumRegulator(random_state=np.random.default_rng(1))

    signals = {"keystroke_variance": 4, "cursor_entropy": 5}
    engine.step(signals)

    previous_state = engine.manifold.state.copy()
    correction = cer.apply(engine)

    assert len(correction) == len(engine.manifold.state)
    assert not np.isnan(correction).any()
    assert not np.array_equal(engine.manifold.state, previous_state)
