"""Steward decision registry for escalation outcomes and governance debt."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence

__all__ = [
    "StewardDecision",
    "EscalationOutcome",
    "DecisionDebt",
    "StewardDecisionRegistry",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class StewardDecision:
    """Explicit, versioned human decision captured for governance."""

    decision_id: str
    version: str
    steward: str
    summary: str
    recorded_at: datetime = field(default_factory=_utc_now)
    outcome: str = "recorded"
    references: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "version": self.version,
            "steward": self.steward,
            "summary": self.summary,
            "recorded_at": self.recorded_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "outcome": self.outcome,
            "references": list(self.references),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EscalationOutcome:
    """Escalation outcome bound to a specific steward decision."""

    escalation_id: str
    decision_id: str
    decision_version: str
    outcome: str
    recorded_at: datetime = field(default_factory=_utc_now)
    notes: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "escalation_id": self.escalation_id,
            "decision_id": self.decision_id,
            "decision_version": self.decision_version,
            "outcome": self.outcome,
            "recorded_at": self.recorded_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class DecisionDebt:
    """Decision debt snapshot for unresolved escalation decisions."""

    count: int
    escalations: tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        return {"count": self.count, "escalations": list(self.escalations)}


class StewardDecisionRegistry:
    """Registry that records steward decisions and binds escalation outcomes."""

    def __init__(self) -> None:
        self._decisions: MutableMapping[str, list[StewardDecision]] = {}
        self._escalation_outcomes: MutableMapping[str, EscalationOutcome] = {}

    def record_decision(self, decision: StewardDecision) -> StewardDecision:
        """Record a steward decision, enforcing version uniqueness."""

        if not decision.decision_id:
            raise ValueError("decision_id must be provided")
        if not decision.version:
            raise ValueError("version must be provided")
        versions = self._decisions.setdefault(decision.decision_id, [])
        if any(entry.version == decision.version for entry in versions):
            raise ValueError(f"decision {decision.decision_id} already has version {decision.version}")
        versions.append(decision)
        return decision

    def decision_versions(self, decision_id: str) -> Sequence[StewardDecision]:
        return tuple(self._decisions.get(decision_id, []))

    def find_decision(self, decision_id: str, version: str) -> StewardDecision | None:
        for entry in self._decisions.get(decision_id, []):
            if entry.version == version:
                return entry
        return None

    def bind_escalation_outcome(
        self,
        escalation_id: str,
        *,
        decision_id: str,
        decision_version: str,
        outcome: str,
        notes: str | None = None,
    ) -> EscalationOutcome:
        """Bind an escalation outcome to a recorded steward decision."""

        decision = self.find_decision(decision_id, decision_version)
        if decision is None:
            raise ValueError("escalation outcome requires an existing decision and version")
        if escalation_id in self._escalation_outcomes:
            raise ValueError(f"escalation {escalation_id} already has a bound outcome")
        outcome_entry = EscalationOutcome(
            escalation_id=escalation_id,
            decision_id=decision_id,
            decision_version=decision_version,
            outcome=outcome,
            notes=notes,
        )
        self._escalation_outcomes[escalation_id] = outcome_entry
        return outcome_entry

    def escalation_outcomes(self) -> Sequence[EscalationOutcome]:
        return tuple(self._escalation_outcomes.values())

    def decision_debt(self, escalations: Iterable[str]) -> DecisionDebt:
        """Return decision debt for escalations without bound decisions."""

        missing = [item for item in escalations if item not in self._escalation_outcomes]
        return DecisionDebt(count=len(missing), escalations=tuple(missing))

    def snapshot(self, escalations: Iterable[str]) -> Dict[str, object]:
        """Return a governance-friendly snapshot for the supplied escalations."""

        debt = self.decision_debt(escalations)
        outcomes = {
            outcome.escalation_id: outcome.to_dict()
            for outcome in self._escalation_outcomes.values()
            if outcome.escalation_id in set(escalations)
        }
        return {
            "escalation_outcomes": outcomes,
            "decision_debt": debt.to_dict(),
        }
