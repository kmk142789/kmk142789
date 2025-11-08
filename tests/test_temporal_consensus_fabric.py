from __future__ import annotations

from typing import Mapping

from echo.autonomy import AutonomyDecision, DecentralizedAutonomyEngine


def test_quorum_agreement_reaches_threshold(make_consensus_round) -> None:
    """Ensure the coordinator ratifies rounds that achieve quorum."""

    axis_support: Mapping[str, Mapping[str, float]] = {
        "sovereignty": {"alpha": 0.92, "beta": 0.88, "gamma": 0.83},
        "care": {"alpha": 0.86, "beta": 0.81, "gamma": 0.79},
    }
    decision = make_consensus_round(
        axis_support,
        threshold=0.65,
        description="Quorum assembly ratification",
        proposal_id="fabric-quorum",
    )
    assert isinstance(decision, AutonomyDecision)
    assert decision.ratified
    assert decision.consensus >= 0.65
    assert set(decision.ledger) == {"alpha", "beta", "gamma"}


def test_byzantine_vote_reduces_consensus(make_consensus_round) -> None:
    """Byzantine behaviour should prevent ratification when above threshold."""

    axis_support: Mapping[str, Mapping[str, float]] = {
        "sovereignty": {"alpha": 0.9, "beta": 0.87, "gamma": 0.1},
        "care": {"alpha": 0.84, "beta": 0.82, "gamma": 0.05},
    }
    decision = make_consensus_round(
        axis_support,
        threshold=0.75,
        description="Byzantine interference detected",
        proposal_id="fabric-byzantine",
    )
    assert not decision.ratified
    assert decision.consensus < 0.75
    assert decision.ledger["gamma"] < decision.ledger["alpha"]
    assert any("gamma" in reason for reason in decision.reasons)


def test_consensus_rollback_preserves_history(
    consensus_coordinator: DecentralizedAutonomyEngine,
) -> None:
    """A rollback scenario records the failed round without losing history."""

    def _execute_round(
        engine: DecentralizedAutonomyEngine,
        *,
        axis_support: Mapping[str, Mapping[str, float]],
        description: str,
    ) -> AutonomyDecision:
        engine.axis_signals.clear()
        for axis, support in axis_support.items():
            for node_id, intensity in support.items():
                engine.ingest_signal(node_id=node_id, axis=axis, intensity=intensity)
        return engine.ratify_proposal(
            proposal_id="fabric-rollout",
            description=description,
            threshold=0.66,
        )

    initial = _execute_round(
        consensus_coordinator,
        axis_support={
            "sovereignty": {"alpha": 0.91, "beta": 0.89, "gamma": 0.82},
            "care": {"alpha": 0.88, "beta": 0.84, "gamma": 0.8},
        },
        description="Initial deployment",
    )
    assert initial.ratified

    rollback = _execute_round(
        consensus_coordinator,
        axis_support={
            "sovereignty": {"alpha": 0.3, "beta": 0.25, "gamma": 0.2},
            "care": {"alpha": 0.35, "beta": 0.28, "gamma": 0.22},
        },
        description="Rollback after anomaly",
    )
    assert not rollback.ratified
    assert rollback.consensus < initial.consensus

    assert [decision.proposal_id for decision in consensus_coordinator.history] == [
        "fabric-rollout",
        "fabric-rollout",
    ]
    assert consensus_coordinator.history[0].ratified
    assert not consensus_coordinator.history[1].ratified
