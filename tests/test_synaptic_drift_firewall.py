import time

from echo.synaptic_drift_firewall import (
    CounterfactualEngine,
    FeatureProjector,
    SignalEnvelope,
    SynapticDriftFirewall,
)


def test_feature_projector_encodes_mixed_payloads():
    projector = FeatureProjector()
    payload = {"alpha": 1, "beta": "mode", "gamma": 3.5}
    vector = projector.encode(payload)
    assert len(vector) >= 6
    assert vector[0] == 1.0
    # Text encoding adds three dimensions; ensure deterministic order (beta sorted before gamma).
    assert vector[1] == len("mode")


def test_counterfactual_engine_generates_probes():
    projector = FeatureProjector()
    engine = CounterfactualEngine(projector)
    history = [[1.0, 2.0, 3.0], [1.2, 1.8, 3.2]]
    current = [2.0, 3.5, 4.0]
    counterfactuals = engine.generate(current, history)
    names = {cf.name for cf in counterfactuals}
    assert names == {"phase_inversion", "volatility_cooling", "temporal_projection"}
    assert all(len(cf.vector) == len(current) for cf in counterfactuals)


def test_firewall_routes_shadow_sim_before_containment():
    firewall = SynapticDriftFirewall(window=5, tolerance=0.2)
    seeds = [
        SignalEnvelope(
            source="telemetry",
            channel="edge-A",
            payload={"latency": 120, "loss": 0.02},
            timestamp=time.time(),
        ),
        SignalEnvelope(
            source="telemetry",
            channel="edge-A",
            payload={"latency": 130, "loss": 0.03},
            timestamp=time.time(),
        ),
    ]
    for seed in seeds:
        firewall.observe(seed)

    probe = SignalEnvelope(
        source="telemetry",
        channel="edge-A",
        payload={"latency": 165, "loss": 0.06},
        timestamp=time.time(),
        importance=1.2,
    )
    decision = firewall.observe(probe)
    assert decision.verdict in {"watch", "contain"}
    assert decision.playbook["action"] in {"shadow_sim", "contain"}


def test_sparse_history_defaults_to_conservative_verdict():
    firewall = SynapticDriftFirewall(window=3, tolerance=0.15)
    probe = SignalEnvelope(
        source="intent",
        channel="policy",
        payload={"mode": "turbo", "budget": 0.9},
        timestamp=time.time(),
        importance=1.8,
    )
    decision = firewall.observe(probe)
    assert decision.verdict in {"watch", "contain"}
    assert decision.score >= 0.0
