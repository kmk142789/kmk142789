"""Time-aware acknowledgment escalation and sovereignty delta reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from ..echo_os_v3 import CycleReport, SovereigntyDeltaReport, build_sovereignty_delta_report
from ..schemas.acknowledgment_registry import (
    AcknowledgmentRecord,
    AcknowledgmentRegistry,
    AcknowledgmentStatus,
)
from .decisions import DecisionDebt, StewardDecisionRegistry

__all__ = [
    "AcknowledgmentSLA",
    "AcknowledgmentEscalation",
    "ScorecardOutcome",
    "EscalationReview",
    "StewardActionReport",
    "AcknowledgmentEscalationEngine",
    "build_steward_action_report",
]


@dataclass(frozen=True)
class AcknowledgmentSLA:
    """Service-level agreement windows for acknowledgment workflows."""

    response: timedelta
    resolution: timedelta | None = None


@dataclass(frozen=True)
class AcknowledgmentEscalation:
    """Escalation payload generated when an SLA is breached."""

    acknowledgment_id: str
    counterparty: str
    status: AcknowledgmentStatus
    reason: str
    deadline: datetime
    breached_at: datetime
    age_hours: float


@dataclass(frozen=True)
class ScorecardOutcome:
    """Scorecard binding that reflects an acknowledgment outcome."""

    acknowledgment_id: str
    pillar: str
    scorecard_item: str
    outcome: str
    updated_at: datetime
    owner: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class EscalationReview:
    """Snapshot of a registry review with SLA escalations."""

    generated_at: datetime
    registry: AcknowledgmentRegistry
    escalations: tuple[AcknowledgmentEscalation, ...]
    scorecard_outcomes: tuple[ScorecardOutcome, ...]
    counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class StewardActionReport:
    """Periodic summary for steward action planning."""

    generated_at: datetime
    escalations: tuple[AcknowledgmentEscalation, ...]
    scorecard_outcomes: tuple[ScorecardOutcome, ...]
    sovereignty_delta: SovereigntyDeltaReport
    notes: str = ""


class AcknowledgmentEscalationEngine:
    """Evaluate acknowledgment SLA compliance and advance statuses."""

    def __init__(self, sla: AcknowledgmentSLA) -> None:
        self._sla = sla

    def review_registry(
        self,
        registry: AcknowledgmentRegistry,
        *,
        now: datetime | None = None,
    ) -> EscalationReview:
        timestamp = now or datetime.now(timezone.utc)
        updated_records: list[AcknowledgmentRecord] = []
        escalations: list[AcknowledgmentEscalation] = []
        scorecard_outcomes: list[ScorecardOutcome] = []

        for record in registry.acknowledgments:
            updated = self._advance_state(record)
            updated_records.append(updated)
            escalations.extend(self._evaluate_escalations(updated, timestamp))
            outcome = self._scorecard_outcome(updated, timestamp)
            if outcome:
                scorecard_outcomes.append(outcome)

        updated_registry = registry.model_copy(update={"acknowledgments": updated_records})
        counts = _count_statuses(updated_records)
        return EscalationReview(
            generated_at=timestamp,
            registry=updated_registry,
            escalations=tuple(escalations),
            scorecard_outcomes=tuple(scorecard_outcomes),
            counts=counts,
        )

    def _advance_state(self, record: AcknowledgmentRecord) -> AcknowledgmentRecord:
        status = record.status
        update: dict[str, object] = {}
        if status == AcknowledgmentStatus.pending and record.acknowledged_at:
            update["status"] = AcknowledgmentStatus.acknowledged
        if (
            status in (AcknowledgmentStatus.acknowledged, AcknowledgmentStatus.pending)
            and record.decision_id
            and record.decision_version
        ):
            update["status"] = AcknowledgmentStatus.resolved
        if update:
            return record.model_copy(update=update)
        return record

    def _evaluate_escalations(
        self, record: AcknowledgmentRecord, now: datetime
    ) -> Sequence[AcknowledgmentEscalation]:
        escalations: list[AcknowledgmentEscalation] = []
        created_at = record.created_at
        response_deadline = created_at + self._sla.response
        if record.status == AcknowledgmentStatus.pending and not record.acknowledged_at:
            if now > response_deadline:
                escalations.append(
                    _build_escalation(
                        record,
                        reason="response_sla_breached",
                        deadline=response_deadline,
                        breached_at=now,
                    )
                )
        if self._sla.resolution:
            if record.status in (AcknowledgmentStatus.pending, AcknowledgmentStatus.acknowledged):
                baseline = record.acknowledged_at or created_at
                resolution_deadline = baseline + self._sla.resolution
                if now > resolution_deadline and record.status != AcknowledgmentStatus.resolved:
                    escalations.append(
                        _build_escalation(
                            record,
                            reason="resolution_sla_breached",
                            deadline=resolution_deadline,
                            breached_at=now,
                        )
                    )
        return escalations

    def _scorecard_outcome(
        self, record: AcknowledgmentRecord, now: datetime
    ) -> ScorecardOutcome | None:
        metadata = record.metadata or {}
        pillar = metadata.get("scorecard_pillar")
        item = metadata.get("scorecard_item")
        if not pillar or not item:
            return None
        if record.status == AcknowledgmentStatus.pending:
            return None
        outcome = record.status.value
        return ScorecardOutcome(
            acknowledgment_id=record.acknowledgment_id,
            pillar=pillar,
            scorecard_item=item,
            outcome=outcome,
            updated_at=now,
            owner=metadata.get("scorecard_owner"),
            notes=metadata.get("scorecard_notes"),
        )


def build_steward_action_report(
    *,
    review: EscalationReview,
    current_cycle: CycleReport,
    previous_cycle: CycleReport | None = None,
    decision_registry: StewardDecisionRegistry | None = None,
    prior_escalation_ids: Iterable[str] | None = None,
) -> StewardActionReport:
    """Build a periodic steward report with sovereignty deltas and escalations."""

    escalation_ids = [item.acknowledgment_id for item in review.escalations]
    decision_debt = _decision_debt(decision_registry, escalation_ids)
    prior_debt = _decision_debt(decision_registry, prior_escalation_ids or [])
    sovereignty_delta = build_sovereignty_delta_report(
        current=current_cycle,
        previous=previous_cycle,
        decision_debt=decision_debt,
        prior_decision_debt=prior_debt,
    )
    notes = _summarize_notes(review, decision_debt)
    return StewardActionReport(
        generated_at=review.generated_at,
        escalations=review.escalations,
        scorecard_outcomes=review.scorecard_outcomes,
        sovereignty_delta=sovereignty_delta,
        notes=notes,
    )


def _decision_debt(
    registry: StewardDecisionRegistry | None, escalation_ids: Iterable[str]
) -> DecisionDebt | None:
    if registry is None:
        return None
    return registry.decision_debt(escalation_ids)


def _build_escalation(
    record: AcknowledgmentRecord,
    *,
    reason: str,
    deadline: datetime,
    breached_at: datetime,
) -> AcknowledgmentEscalation:
    age_hours = (breached_at - record.created_at).total_seconds() / 3600.0
    return AcknowledgmentEscalation(
        acknowledgment_id=record.acknowledgment_id,
        counterparty=record.counterparty,
        status=record.status,
        reason=reason,
        deadline=deadline,
        breached_at=breached_at,
        age_hours=age_hours,
    )


def _count_statuses(records: Iterable[AcknowledgmentRecord]) -> dict[str, int]:
    counts = {status.value: 0 for status in AcknowledgmentStatus}
    for record in records:
        counts[record.status.value] = counts.get(record.status.value, 0) + 1
    return counts


def _summarize_notes(review: EscalationReview, decision_debt: DecisionDebt | None) -> str:
    debt = decision_debt.count if decision_debt else 0
    if review.escalations:
        return f"{len(review.escalations)} escalation(s) pending; decision debt={debt}."
    return f"No escalations pending; decision debt={debt}."
