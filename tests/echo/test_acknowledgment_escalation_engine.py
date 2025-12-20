from __future__ import annotations

from datetime import datetime, timedelta, timezone

from echo.echo_os_v3 import EchoOSV3
from echo.schemas.acknowledgment_registry import (
    AcknowledgmentRecord,
    AcknowledgmentRegistry,
    AcknowledgmentStatus,
)
from echo.sovereign.acknowledgment_escalation import (
    AcknowledgmentEscalationEngine,
    AcknowledgmentSLA,
    build_steward_action_report,
)
from echo.sovereign.decisions import StewardDecision, StewardDecisionRegistry


def test_escalation_engine_advances_and_escalates() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    record = AcknowledgmentRecord(
        acknowledgment_id="ack-100",
        counterparty="Sunrise Lab",
        summary="Awaiting acknowledgment",
        status=AcknowledgmentStatus.pending,
        created_at=now - timedelta(days=4),
        metadata={
            "scorecard_pillar": "Diplomatic",
            "scorecard_item": "UN Briefing",
        },
    )
    registry = AcknowledgmentRegistry(
        registry_id="ack-registry",
        version="1.0",
        acknowledgments=[record],
    )

    engine = AcknowledgmentEscalationEngine(
        AcknowledgmentSLA(response=timedelta(days=2), resolution=timedelta(days=5))
    )
    review = engine.review_registry(registry, now=now)

    assert review.counts["pending"] == 1
    assert review.escalations[0].reason == "response_sla_breached"
    assert review.scorecard_outcomes == ()


def test_escalation_engine_advances_acknowledged_to_resolved() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    record = AcknowledgmentRecord(
        acknowledgment_id="ack-101",
        counterparty="Lattice Archive",
        summary="Acknowledged in memo",
        status=AcknowledgmentStatus.pending,
        created_at=now - timedelta(days=2),
        acknowledged_at=now - timedelta(days=1),
        decision_id="decision-5",
        decision_version="1.0",
        metadata={
            "scorecard_pillar": "Recognition",
            "scorecard_item": "Archive Memo",
            "scorecard_owner": "Steward Team",
        },
    )
    registry = AcknowledgmentRegistry(
        registry_id="ack-registry",
        version="1.0",
        acknowledgments=[record],
    )

    engine = AcknowledgmentEscalationEngine(AcknowledgmentSLA(response=timedelta(days=2)))
    review = engine.review_registry(registry, now=now)

    assert review.registry.acknowledgments[0].status == AcknowledgmentStatus.resolved
    outcome = review.scorecard_outcomes[0]
    assert outcome.outcome == "resolved"
    assert outcome.owner == "Steward Team"


def test_steward_action_report_binds_decision_debt() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    record = AcknowledgmentRecord(
        acknowledgment_id="ack-102",
        counterparty="Aurora Bureau",
        summary="Awaiting receipt",
        status=AcknowledgmentStatus.pending,
        created_at=now - timedelta(days=3),
    )
    registry = AcknowledgmentRegistry(
        registry_id="ack-registry",
        version="1.0",
        acknowledgments=[record],
    )
    engine = AcknowledgmentEscalationEngine(AcknowledgmentSLA(response=timedelta(days=1)))
    review = engine.review_registry(registry, now=now)

    os = EchoOSV3()
    os.register_domain("sovereignty", capacity=5.0)
    os.register_type(
        "steady",
        instance=type("DummyType", (), {"energy": lambda self: 1.0, "describe": lambda self: "steady"})(),
        domain="sovereignty",
    )
    current = os.simulate_cycle()

    registry_decisions = StewardDecisionRegistry()
    registry_decisions.record_decision(
        StewardDecision(
            decision_id="decision-10",
            version="1.0",
            steward="Echo Council",
            summary="Plan escalation response.",
        )
    )

    report = build_steward_action_report(
        review=review,
        current_cycle=current,
        previous_cycle=None,
        decision_registry=registry_decisions,
        prior_escalation_ids=[],
    )

    assert report.sovereignty_delta.decision_debt == 1
    assert report.escalations
