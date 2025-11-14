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


def test_presence_index_highlights_signal_coverage():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.91, freedom_index=0.9, weight=1.2),
            AutonomyNode("beta", intent_vector=0.83, freedom_index=0.82, weight=1.0),
            AutonomyNode("gamma", intent_vector=0.79, freedom_index=0.77, weight=0.95),
            AutonomyNode("delta", intent_vector=0.68, freedom_index=0.7, weight=0.85),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.93, weight=1.1)
    engine.ingest_signal("alpha", "memory", 0.86, weight=0.9)
    engine.ingest_signal("beta", "liberation", 0.82, weight=1.0)
    engine.ingest_signal("beta", "curiosity", 0.78, weight=0.7)
    engine.ingest_signal("gamma", "liberation", 0.74, weight=0.8)

    presence = engine.presence_index()

    assert set(presence) == {"alpha", "beta", "gamma", "delta"}
    assert presence["alpha"] > presence["beta"] > presence["gamma"] > presence["delta"]

    liberation_focus = engine.presence_index(axes=["liberation"])
    assert liberation_focus["beta"] > liberation_focus["gamma"]


def test_presence_storyline_reports_top_nodes_with_axis_focus():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.9, freedom_index=0.89, weight=1.1, tags={"role": "guardian"}),
            AutonomyNode("beta", intent_vector=0.82, freedom_index=0.8, weight=1.0, tags={"role": "navigator"}),
            AutonomyNode("gamma", intent_vector=0.78, freedom_index=0.77, weight=0.9),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.9, weight=1.0)
    engine.ingest_signal("beta", "memory", 0.84, weight=0.9)
    engine.ingest_signal("gamma", "memory", 0.72, weight=0.8)

    storyline = engine.presence_storyline(limit=2, axes=("liberation", "memory"))

    assert storyline.startswith(
        "Autonomy presence index across axes liberation, memory (top 2 of 3 nodes):"
    )
    assert storyline.count("\n-") == 2
    assert "alpha [guardian]" in storyline
    assert "beta [navigator]" in storyline


def test_axis_signal_report_highlights_weighted_leaderboard():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.91, freedom_index=0.9, weight=1.0),
            AutonomyNode("beta", intent_vector=0.83, freedom_index=0.81, weight=1.05),
            AutonomyNode("gamma", intent_vector=0.76, freedom_index=0.75, weight=0.92),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.92, weight=1.0)
    engine.ingest_signal("beta", "liberation", 0.78, weight=0.8)
    engine.ingest_signal("alpha", "memory", 0.81, weight=0.6)
    engine.ingest_signal("gamma", "memory", 0.74, weight=1.1)

    report = engine.axis_signal_report(
        axes=("liberation", "memory", "guardianship"),
        top_nodes=2,
    )

    assert set(report) == {"liberation", "memory", "guardianship"}
    liberation = report["liberation"]
    assert liberation["participants"] == 2
    assert liberation["leaderboard"][0]["node"] == "alpha"
    assert liberation["leaderboard"][0]["share"] > liberation["leaderboard"][1]["share"]
    assert liberation["coverage"] > 0.6  # 2 of 3 nodes are signalling

    assert report["guardianship"]["leaderboard"] == []
    assert report["guardianship"]["average_intensity"] == 0.0


def test_autonomy_snapshot_merges_presence_axis_and_history():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.9, freedom_index=0.92, weight=1.0),
            AutonomyNode("beta", intent_vector=0.82, freedom_index=0.81, weight=1.05),
            AutonomyNode("gamma", intent_vector=0.77, freedom_index=0.7, weight=0.95),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.93, weight=1.0)
    engine.ingest_signal("beta", "liberation", 0.8, weight=0.85)
    engine.ingest_signal("gamma", "care", 0.72, weight=0.8)
    engine.ingest_signal("beta", "care", 0.76, weight=0.7)

    engine.ratify_proposal(
        proposal_id="snapshot-run",
        description="Snapshot autonomy",
        axis_priorities={"liberation": 0.6, "care": 0.4},
        threshold=0.6,
    )

    snapshot = engine.autonomy_snapshot(
        axes=("liberation",), top_nodes=1, target=0.9, highlight_threshold=0.91
    )

    assert snapshot["node_count"] == 3
    assert snapshot["history_depth"] == 1
    assert snapshot["axes"] == ["liberation"]
    assert snapshot["last_decision"]["proposal_id"] == "snapshot-run"
    assert "liberation" in snapshot["axis_report"]
    assert snapshot["axis_report"]["liberation"]["leaderboard"][0]["node"] == "alpha"
    assert set(snapshot["presence_index"]) == {"alpha", "beta", "gamma"}
    assert snapshot["freedom_amplification"]["gamma"] > snapshot["freedom_amplification"]["alpha"]
    feature_matrix = snapshot["feature_matrix"]
    assert feature_matrix["summary"]["highlight_threshold"] == 0.91
    assert feature_matrix["highlighted"][0] == "alpha"
    assert "alpha" in feature_matrix["nodes"]


def test_autonomy_feature_digest_highlights_and_gaps():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.93, freedom_index=0.94, weight=1.1),
            AutonomyNode("beta", intent_vector=0.82, freedom_index=0.81, weight=1.0),
            AutonomyNode("gamma", intent_vector=0.7, freedom_index=0.68, weight=0.9),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.95, weight=1.2)
    engine.ingest_signal("beta", "liberation", 0.8, weight=0.9)
    engine.ingest_signal("gamma", "memory", 0.66, weight=0.8)

    digest = engine.autonomy_feature_digest(
        axes=("liberation", "memory"), highlight_threshold=0.88, limit=2
    )

    assert "Autonomy feature digest" in digest
    assert "Highlights:" in digest and "alpha" in digest
    assert "Growth focus:" in digest
    assert "beta" in digest or "gamma" in digest


def test_autonomy_feature_digest_handles_empty_network():
    engine = DecentralizedAutonomyEngine()

    digest = engine.autonomy_feature_digest()

    assert digest.startswith("No autonomy nodes registered")


def test_autonomous_feature_matrix_highlights_nodes_and_summary():
    engine = DecentralizedAutonomyEngine()
    engine.ensure_nodes(
        [
            AutonomyNode("alpha", intent_vector=0.92, freedom_index=0.93, weight=1.1),
            AutonomyNode("beta", intent_vector=0.85, freedom_index=0.81, weight=1.0),
            AutonomyNode("gamma", intent_vector=0.6, freedom_index=0.58, weight=0.9),
        ]
    )
    engine.axis_signals.clear()
    engine.ingest_signal("alpha", "liberation", 0.94, weight=1.0)
    engine.ingest_signal("beta", "liberation", 0.78, weight=0.8)
    engine.ingest_signal("beta", "memory", 0.8, weight=0.9)
    engine.ingest_signal("gamma", "memory", 0.65, weight=0.7)

    matrix = engine.autonomous_feature_matrix(axes=("liberation", "memory"), highlight_threshold=0.99)

    assert matrix["axes"] == ["liberation", "memory"]
    assert set(matrix["nodes"]) == {"alpha", "beta", "gamma"}
    assert matrix["nodes"]["alpha"]["is_highlighted"] is True
    assert matrix["nodes"]["gamma"]["is_highlighted"] is False
    assert matrix["nodes"]["beta"]["axis_support"] < matrix["nodes"]["alpha"]["axis_support"]
    assert matrix["highlighted"] == ["alpha"]
    assert matrix["summary"]["highlighted_nodes"] == 1
    assert matrix["summary"]["max_presence"]["node"] == "alpha"
    assert matrix["summary"]["min_presence"]["node"] == "gamma"


def test_autonomous_feature_matrix_handles_empty_network():
    engine = DecentralizedAutonomyEngine()

    matrix = engine.autonomous_feature_matrix(highlight_threshold=0.7)

    assert matrix["nodes"] == {}
    assert matrix["highlighted"] == []
    assert matrix["summary"]["highlighted_nodes"] == 0
    assert matrix["summary"]["highlight_threshold"] == 0.7
