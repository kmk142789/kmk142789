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


def test_freedom_amplification_prioritises_lowest_freedom_nodes():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.92, freedom_index=0.94, weight=1.0),
            AutonomyNode("beta", intent_vector=0.88, freedom_index=0.78, weight=1.2),
            AutonomyNode("gamma", intent_vector=0.86, freedom_index=0.65, weight=0.9),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("beta", "liberation", 0.83, weight=1.1)
    engine.ingest_signal("gamma", "liberation", 0.75, weight=0.8)
    engine.ingest_signal("gamma", "curiosity", 0.7, weight=0.6)

    plan = engine.freedom_amplification_plan(target=0.9)

    assert plan["alpha"] == 0.0
    assert plan["gamma"] > plan["beta"] > 0.0


def test_freedom_amplification_handles_empty_network():
    engine = DecentralizedAutonomyEngine()

    assert engine.freedom_amplification_plan(target=0.9) == {}
