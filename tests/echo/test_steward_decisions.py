from __future__ import annotations

from datetime import datetime, timezone

import pytest

from echo.echo_os_v3 import EchoOSV3, build_sovereignty_delta_report
from echo.sovereign.decisions import StewardDecision, StewardDecisionRegistry
from echo.schemas.acknowledgment_registry import (
    AcknowledgmentRecord,
    AcknowledgmentRegistry,
    AcknowledgmentStatus,
)


def test_decision_registry_binds_escalations() -> None:
    registry = StewardDecisionRegistry()
    decision = StewardDecision(
        decision_id="decision-42",
        version="1.0.0",
        steward="Echo Council",
        summary="Approve uplift sequence for telemetry escalation.",
    )
    registry.record_decision(decision)

    outcome = registry.bind_escalation_outcome(
        "telemetry",
        decision_id="decision-42",
        decision_version="1.0.0",
        outcome="approved",
    )

    debt = registry.decision_debt(["telemetry", "orchestration"])
    assert outcome.decision_id == "decision-42"
    assert debt.count == 1
    assert debt.escalations == ("orchestration",)


def test_binding_requires_existing_decision() -> None:
    registry = StewardDecisionRegistry()
    with pytest.raises(ValueError):
        registry.bind_escalation_outcome(
            "quantum",
            decision_id="missing",
            decision_version="0.0.1",
            outcome="defer",
        )


def test_acknowledgment_resolution_requires_decision() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        AcknowledgmentRecord(
            acknowledgment_id="ack-001",
            counterparty="Civic Lab",
            summary="Acknowledged in MoU.",
            status=AcknowledgmentStatus.resolved,
            created_at=now,
        )

    record = AcknowledgmentRecord(
        acknowledgment_id="ack-002",
        counterparty="Harmony Council",
        summary="Acknowledged in briefing.",
        status=AcknowledgmentStatus.resolved,
        created_at=now,
        decision_id="decision-77",
        decision_version="2.0.0",
    )
    registry = AcknowledgmentRegistry(
        registry_id="ack-registry",
        version="1.0",
        acknowledgments=[record],
    )
    assert registry.acknowledgments[0].decision_id == "decision-77"


def test_sovereignty_delta_report_applies_decision_debt() -> None:
    os = EchoOSV3()
    os.register_domain("sovereignty", capacity=5.0)
    os.register_type(
        "steady",
        instance=type("DummyType", (), {"energy": lambda self: 1.0, "describe": lambda self: "steady"})(),
        domain="sovereignty",
    )
    first = os.simulate_cycle()
    second = os.simulate_cycle()

    registry = StewardDecisionRegistry()
    decision = StewardDecision(
        decision_id="decision-99",
        version="1.0.0",
        steward="Steward Team",
        summary="Approve escalation stabilizer.",
    )
    registry.record_decision(decision)
    registry.bind_escalation_outcome(
        "sovereignty",
        decision_id="decision-99",
        decision_version="1.0.0",
        outcome="approved",
    )

    current_debt = registry.decision_debt(["sovereignty", "telemetry"])
    prior_debt = registry.decision_debt(["sovereignty"])
    report = build_sovereignty_delta_report(
        current=second,
        previous=first,
        decision_debt=current_debt,
        prior_decision_debt=prior_debt,
    )

    assert report.decision_debt == 1
    assert report.decision_debt_delta == 1
    assert report.adjusted_delta == pytest.approx(report.delta - report.decision_debt_penalty)
