import math

from src.unclassifiable_force_engine import (
    FusionOutcome,
    MythogenicDrift,
    ParadoxReciprocity,
    UnclassifiableFusionEngine,
)


def test_mythogenic_drift_and_paradox_reciprocity_metrics():
    drift = MythogenicDrift(3.2, 0.75, recursion_depth=2)
    reciprocity = ParadoxReciprocity(1.4, 0.9, 0.6)

    assert math.isclose(drift.potential(), 0.9243579334004886, rel_tol=1e-12)
    assert math.isclose(reciprocity.strain(), 1.4541420677843435, rel_tol=1e-12)


def test_unclassifiable_fusion_engine_outputs_tuple_view():
    drift = MythogenicDrift(-1.1, -0.25, recursion_depth=0)
    reciprocity = ParadoxReciprocity(-0.8, 1.2, -1.0)
    engine = UnclassifiableFusionEngine(drift, reciprocity)

    outcome = engine.fuse()
    assert isinstance(outcome, FusionOutcome)
    fusion_index, anomaly_gradient, equilibrium = outcome.as_tuple()

    assert math.isclose(fusion_index, 0.38559329314841256, rel_tol=1e-12)
    assert math.isclose(anomaly_gradient, 0.2443938080874566, rel_tol=1e-12)
    assert math.isclose(equilibrium, 0.1798607244280992, rel_tol=1e-12)
