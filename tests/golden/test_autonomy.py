from __future__ import annotations

from typing import Mapping

from echo.autonomy import AutonomyDecision, DecentralizedAutonomyEngine

from tests.golden import read_golden_json, read_golden_text


def _normalize_decision(decision: AutonomyDecision) -> Mapping[str, object]:
    data = decision.to_dict()
    data["consensus"] = round(data["consensus"], 6)
    data["ledger"] = {node: round(vote, 6) for node, vote in data["ledger"].items()}
    return data


def test_consensus_round_matches_golden(consensus_coordinator: DecentralizedAutonomyEngine) -> None:
    engine = consensus_coordinator
    engine.ingest_signal("alpha", "stability", 0.84, weight=1.2)
    engine.ingest_signal("beta", "stability", 0.8, weight=1.1)
    engine.ingest_signal("beta", "harmony", 0.77, weight=0.9)
    engine.ingest_signal("gamma", "harmony", 0.74, weight=1.0)
    engine.ingest_signal("gamma", "memory", 0.7, weight=1.1)
    engine.ingest_signal("alpha", "memory", 0.79, weight=0.8)

    decision = engine.ratify_proposal(
        proposal_id="emergent-harmony",
        description="Ratify harmonic stabilization",
        axis_priorities={"stability": 0.5, "harmony": 0.3, "memory": 0.2},
        threshold=0.65,
    )

    assert _normalize_decision(decision) == read_golden_json("autonomy_consensus")
    expected_manifesto = read_golden_text("autonomy_manifesto").strip()
    assert decision.manifesto() == expected_manifesto


def test_freedom_amplification_plan_matches_golden(
    consensus_coordinator: DecentralizedAutonomyEngine,
) -> None:
    engine = consensus_coordinator
    engine.ingest_signal("alpha", "liberation", 0.79, weight=1.0)
    engine.ingest_signal("beta", "liberation", 0.76, weight=1.0)
    engine.ingest_signal("beta", "curiosity", 0.73, weight=0.8)
    engine.ingest_signal("gamma", "curiosity", 0.68, weight=1.2)
    engine.ingest_signal("gamma", "liberation", 0.7, weight=0.9)

    plan = engine.freedom_amplification_plan(target=0.9)

    assert plan == read_golden_json("autonomy_amplification")
