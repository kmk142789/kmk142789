from echo.autonomy import (
    AutonomyDecision,
    AutonomyNode,
    DecentralizedAutonomyEngine,
)


def test_autonomy_engine_ratifes_with_balanced_nodes():
    engine = DecentralizedAutonomyEngine()
    nodes = [
        AutonomyNode("alpha", intent_vector=0.9, freedom_index=0.92, weight=1.2),
        AutonomyNode("beta", intent_vector=0.85, freedom_index=0.88, weight=1.1),
        AutonomyNode("gamma", intent_vector=0.83, freedom_index=0.9, weight=1.0),
    ]
    engine.ensure_nodes(nodes)
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.9, weight=1.0)
    engine.ingest_signal("beta", "memory", 0.82, weight=0.9)
    engine.ingest_signal("gamma", "curiosity", 0.84, weight=1.1)

    decision = engine.ratify_proposal(
        proposal_id="test",
        description="test autonomy",
        axis_priorities={"liberation": 0.4, "memory": 0.3, "curiosity": 0.3},
        threshold=0.6,
    )

    assert isinstance(decision, AutonomyDecision)
    assert decision.ratified is True
    assert 0.6 <= decision.consensus <= 1.0
    assert set(decision.ledger) == {"alpha", "beta", "gamma"}
    assert decision.axis_weights["liberation"] > decision.axis_weights["memory"]
    assert "axis=" in decision.reasons[0]
    assert "Proposal test" in decision.manifesto()


def test_axis_weights_populated_from_signals_when_missing():
    engine = DecentralizedAutonomyEngine()
    engine.register_node(AutonomyNode("solo", intent_vector=0.7, freedom_index=0.8))
    engine.axis_signals.clear()
    engine.ingest_signal("solo", "guardianship", 0.66, weight=1.0)

    decision = engine.ratify_proposal(
        proposal_id="solo", description="solo run", axis_priorities=None, threshold=0.5
    )

    assert decision.axis_weights["guardianship"] == 1.0
    assert decision.consensus >= 0.5
