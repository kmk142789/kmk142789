import math

import pytest

from src.omega_ascendancy_engine import (
    BeliefFiber,
    CausalResonanceTensor,
    OmegaAscendancyEngine,
)


def test_projection_is_deterministic_with_seed():
    engine_a = OmegaAscendancyEngine(seed=11)
    engine_b = OmegaAscendancyEngine(seed=11)
    obs = [0.2, -0.3, 0.5]
    fibers_a = engine_a.ingest(obs, timestamp=1)
    fibers_b = engine_b.ingest(obs, timestamp=1)
    assert [f.values for f in fibers_a] == [f.values for f in fibers_b]
    assert engine_a.coherence_trace() == engine_b.coherence_trace()


def test_drift_inversion_reduces_magnitude():
    engine = OmegaAscendancyEngine(seed=3)
    base_fiber = BeliefFiber("baseline", 1, (0.5, -0.2), timestamp=0)
    tensor = CausalResonanceTensor()
    tensor.update([base_fiber])
    candidate = BeliefFiber("candidate", 1, (0.8, -0.7), timestamp=0)
    stabilized, drift = engine.drift_inverter.stabilize(base_fiber, candidate)
    corrected_drift = math.sqrt(sum((b - c) ** 2 for b, c in zip(base_fiber.values, stabilized.values)))
    assert corrected_drift < drift


def test_resonance_gating_filters_low_coherence():
    engine = OmegaAscendancyEngine(seed=5, coherence_threshold=0.7)
    baseline = BeliefFiber("b", 1, (1.0, 0.0), timestamp=0)
    aligned = BeliefFiber("aligned", 1, (0.9, 0.0), timestamp=0)
    orthogonal = BeliefFiber("orthogonal", 1, (0.0, 1.0), timestamp=0)
    gated = engine.arbiter.gate([baseline, aligned, orthogonal])
    ids = {f.identifier for f in gated}
    assert "orthogonal" not in ids
    assert "aligned" in ids


def test_energy_normalization_bounds_high_scale():
    high_scale = BeliefFiber("high", 7, (1.0, 1.0, 1.0), timestamp=0)
    low_scale = BeliefFiber("low", 1, (1.0, 1.0, 1.0), timestamp=0)
    assert high_scale.energy() < low_scale.energy()


def test_multi_step_integration_traces_are_monotonic():
    engine = OmegaAscendancyEngine(seed=13)
    obs = [1.0, 0.5, -0.25]
    for t in range(3):
        engine.ingest(obs, timestamp=t)
    coherence_trace = engine.coherence_trace()
    drift_trace = engine.drift_trace()
    assert all(0.0 <= c <= 1.0 for c in coherence_trace)
    assert all(d >= 0.0 for d in drift_trace)
    assert len(coherence_trace) == len(drift_trace) == len(engine.energy_trace())
