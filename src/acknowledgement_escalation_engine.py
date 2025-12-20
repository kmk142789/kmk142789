"""Time-aware acknowledgement escalation and sovereignty reporting engine."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "AcknowledgementRecord",
    "EscalationStep",
    "EscalationPolicy",
    "AcknowledgementOutcome",
    "EscalationRun",
    "ScorecardEntry",
    "SovereigntyDeltaReport",
    "AcknowledgementEscalationEngine",
    "build_delta_report",
    "load_scorecard",
    "save_scorecard",
]


@dataclass(frozen=True)
class EscalationStep:
    """Represents an escalation action at a ratio of the SLA."""

    name: str
    threshold_ratio: float
    action: str


@dataclass(frozen=True)
class EscalationPolicy:
    """Defines how acknowledgements should escalate against an SLA."""

    steps: tuple[EscalationStep, ...] = (
        EscalationStep(
            name="reminder",
            threshold_ratio=0.5,
            action="Send reminder and reconfirm acknowledgement expectations.",
        ),
        EscalationStep(
            name="escalate",
            threshold_ratio=0.9,
            action="Escalate to steward with counterparty context.",
        ),
    )


@dataclass
class AcknowledgementRecord:
    """Tracks a single acknowledgement request and its SLA."""

    reference: str
    counterparty: str
    channel: str
    submitted_at: datetime
    sla_hours: float
    state: str = "submitted"
    acknowledged_at: datetime | None = None
    last_contact_at: datetime | None = None
    scorecard_metric: str | None = None
    notes: str | None = None

    def response_deadline(self) -> datetime:
        return _ensure_timezone(self.submitted_at) + timedelta(hours=self.sla_hours)

    def age_hours(self, now: datetime) -> float:
        now = _ensure_timezone(now)
        submitted_at = _ensure_timezone(self.submitted_at)
        return max((now - submitted_at).total_seconds() / 3600.0, 0.0)


@dataclass(frozen=True)
class AcknowledgementOutcome:
    """Outcome of evaluating a record against SLA policy."""

    reference: str
    counterparty: str
    channel: str
    state: str
    response_deadline: datetime
    triggered_steps: tuple[EscalationStep, ...]
    breach: bool
    scorecard_metric: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class EscalationRun:
    """Aggregated outcome for an SLA evaluation run."""

    evaluated_at: datetime
    outcomes: tuple[AcknowledgementOutcome, ...]
    escalations: tuple[AcknowledgementOutcome, ...]
    breaches: tuple[AcknowledgementOutcome, ...]


@dataclass
class ScorecardEntry:
    """Represents a sovereignty scorecard entry."""

    category: str
    metric: str
    description: str
    target: str
    current_status: str
    last_updated: str
    notes: str

    @property
    def metric_key(self) -> str:
        return f"{self.category}:{self.metric}"


@dataclass(frozen=True)
class SovereigntyDeltaReport:
    """Delta report summarising changes and escalation actions."""

    generated_at: datetime
    changes: tuple[dict[str, str], ...]
    escalations: tuple[dict[str, str], ...]
    breaches: tuple[dict[str, str], ...]
    steward_actions: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "generated_at": _format_date(self.generated_at),
            "changes": list(self.changes),
            "escalations": list(self.escalations),
            "breaches": list(self.breaches),
            "steward_actions": list(self.steward_actions),
        }

    def render_markdown(self) -> str:
        lines = [
            f"# Sovereignty Delta Report ({_format_date(self.generated_at)})",
            "",
            "## Scorecard Changes",
        ]
        if not self.changes:
            lines.append("- No scorecard updates this cycle.")
        else:
            for change in self.changes:
                lines.append(
                    f"- **{change['metric']}**: {change['previous_status']} →"
                    f" {change['current_status']}"
                )
        lines.extend(["", "## Escalations"])
        if not self.escalations:
            lines.append("- No active escalations.")
        else:
            for escalation in self.escalations:
                lines.append(
                    f"- {escalation['reference']} ({escalation['counterparty']}):"
                    f" {escalation['state']}"
                )
        lines.extend(["", "## SLA Breaches"])
        if not self.breaches:
            lines.append("- No SLA breaches.")
        else:
            for breach in self.breaches:
                lines.append(
                    f"- {breach['reference']} ({breach['counterparty']}):"
                    f" {breach['state']}"
                )
        lines.extend(["", "## Steward Actions"])
        if not self.steward_actions:
            lines.append("- No steward actions required.")
        else:
            for action in self.steward_actions:
                lines.append(f"- {action}")
        return "\n".join(lines)


class AcknowledgementEscalationEngine:
    """Evaluate acknowledgements, enforce SLA cadence, and update scorecards."""

    def __init__(self, *, policy: EscalationPolicy | None = None) -> None:
        self.policy = policy or EscalationPolicy()

    def evaluate(
        self, records: Sequence[AcknowledgementRecord], *, now: datetime | None = None
    ) -> EscalationRun:
        if now is None:
            now = datetime.now(timezone.utc)
        now = _ensure_timezone(now)

        outcomes: list[AcknowledgementOutcome] = []
        escalations: list[AcknowledgementOutcome] = []
        breaches: list[AcknowledgementOutcome] = []

        for record in records:
            outcome = self._evaluate_record(record, now)
            outcomes.append(outcome)
            if outcome.breach:
                breaches.append(outcome)
            elif outcome.triggered_steps:
                escalations.append(outcome)

        return EscalationRun(
            evaluated_at=now,
            outcomes=tuple(outcomes),
            escalations=tuple(escalations),
            breaches=tuple(breaches),
        )

    def _evaluate_record(
        self, record: AcknowledgementRecord, now: datetime
    ) -> AcknowledgementOutcome:
        deadline = record.response_deadline()
        triggered_steps: list[EscalationStep] = []
        breach = False

        if record.acknowledged_at:
            state = "acknowledged"
        else:
            age_hours = record.age_hours(now)
            if record.sla_hours > 0:
                age_ratio = age_hours / record.sla_hours
            else:
                age_ratio = 0.0

            for step in self.policy.steps:
                if age_ratio >= step.threshold_ratio:
                    triggered_steps.append(step)

            breach = age_ratio >= 1.0
            if breach:
                state = "breached"
            elif triggered_steps:
                state = "escalated"
            elif age_ratio > 0:
                state = "in_flight"
            else:
                state = record.state or "submitted"

        return AcknowledgementOutcome(
            reference=record.reference,
            counterparty=record.counterparty,
            channel=record.channel,
            state=state,
            response_deadline=deadline,
            triggered_steps=tuple(triggered_steps),
            breach=breach,
            scorecard_metric=record.scorecard_metric,
            notes=record.notes,
        )

    def bind_to_scorecard(
        self,
        entries: Sequence[ScorecardEntry],
        run: EscalationRun,
        *,
        now: datetime | None = None,
    ) -> tuple[ScorecardEntry, ...]:
        if now is None:
            now = run.evaluated_at
        now = _ensure_timezone(now)

        entry_map = {entry.metric_key: entry for entry in entries}
        updated_entries: list[ScorecardEntry] = []
        for entry in entries:
            updated_entries.append(entry)

        for outcome in run.outcomes:
            if not outcome.scorecard_metric:
                continue
            entry = _match_scorecard_entry(entry_map, outcome.scorecard_metric)
            if entry is None:
                continue
            updated_entry = _apply_outcome_to_entry(entry, outcome, now)
            entry_map[entry.metric_key] = updated_entry

        return tuple(entry_map.values())


def load_scorecard(path: Path) -> tuple[ScorecardEntry, ...]:
    rows: list[ScorecardEntry] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                ScorecardEntry(
                    category=row.get("Category", ""),
                    metric=row.get("Metric", ""),
                    description=row.get("Description", ""),
                    target=row.get("Target", ""),
                    current_status=row.get("Current_Status", ""),
                    last_updated=row.get("Last_Updated", ""),
                    notes=row.get("Notes", ""),
                )
            )
    return tuple(rows)


def save_scorecard(path: Path, entries: Iterable[ScorecardEntry]) -> None:
    fieldnames = [
        "Category",
        "Metric",
        "Description",
        "Target",
        "Current_Status",
        "Last_Updated",
        "Notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "Category": entry.category,
                    "Metric": entry.metric,
                    "Description": entry.description,
                    "Target": entry.target,
                    "Current_Status": entry.current_status,
                    "Last_Updated": entry.last_updated,
                    "Notes": entry.notes,
                }
            )


def build_delta_report(
    previous: Sequence[ScorecardEntry],
    updated: Sequence[ScorecardEntry],
    run: EscalationRun,
    *,
    now: datetime | None = None,
) -> SovereigntyDeltaReport:
    if now is None:
        now = run.evaluated_at
    now = _ensure_timezone(now)

    previous_map = {entry.metric_key: entry for entry in previous}
    changes: list[dict[str, str]] = []
    for entry in updated:
        prior = previous_map.get(entry.metric_key)
        if prior is None:
            continue
        if (
            prior.current_status != entry.current_status
            or prior.notes != entry.notes
            or prior.last_updated != entry.last_updated
        ):
            changes.append(
                {
                    "metric": entry.metric_key,
                    "previous_status": prior.current_status,
                    "current_status": entry.current_status,
                    "notes": entry.notes,
                }
            )

    escalations = _summarize_outcomes(run.escalations)
    breaches = _summarize_outcomes(run.breaches)
    steward_actions = _build_steward_actions(run)

    return SovereigntyDeltaReport(
        generated_at=now,
        changes=tuple(changes),
        escalations=tuple(escalations),
        breaches=tuple(breaches),
        steward_actions=tuple(steward_actions),
    )


def _summarize_outcomes(
    outcomes: Sequence[AcknowledgementOutcome],
) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for outcome in outcomes:
        summary.append(
            {
                "reference": outcome.reference,
                "counterparty": outcome.counterparty,
                "state": outcome.state,
                "deadline": _format_date(outcome.response_deadline),
            }
        )
    return summary


def _build_steward_actions(run: EscalationRun) -> list[str]:
    actions: list[str] = []
    for outcome in run.escalations:
        for step in outcome.triggered_steps:
            actions.append(
                f"{outcome.reference}: {step.action} (counterparty: {outcome.counterparty})"
            )
    for outcome in run.breaches:
        actions.append(
            f"{outcome.reference}: SLA breached, escalate to stewardship council."
        )
    return actions


def _match_scorecard_entry(
    entry_map: dict[str, ScorecardEntry], metric_key: str
) -> ScorecardEntry | None:
    if metric_key in entry_map:
        return entry_map[metric_key]
    for entry in entry_map.values():
        if entry.metric == metric_key:
            return entry
    return None


def _apply_outcome_to_entry(
    entry: ScorecardEntry, outcome: AcknowledgementOutcome, now: datetime
) -> ScorecardEntry:
    status = _status_for_outcome(entry.current_status, outcome)
    notes = _merge_notes(entry.notes, outcome, now)
    return ScorecardEntry(
        category=entry.category,
        metric=entry.metric,
        description=entry.description,
        target=entry.target,
        current_status=status,
        last_updated=_format_date(now),
        notes=notes,
    )


def _status_for_outcome(existing_status: str, outcome: AcknowledgementOutcome) -> str:
    if outcome.state == "acknowledged":
        return "Acknowledged"
    if outcome.state == "breached":
        return "Escalated (SLA breach)"
    if outcome.state == "escalated":
        return "Escalated"
    if outcome.state == "in_flight":
        return "Pending acknowledgement"
    return existing_status


def _merge_notes(existing: str, outcome: AcknowledgementOutcome, now: datetime) -> str:
    stamp = _format_date(now)
    summary = (
        f"Ack {outcome.counterparty} via {outcome.channel}:"
        f" {outcome.state} (deadline {_format_date(outcome.response_deadline)})."
    )
    if outcome.notes:
        summary = f"{summary} {outcome.notes}"
    if existing:
        return f"{existing} | {stamp}: {summary}"
    return f"{stamp}: {summary}"


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_date(value: datetime) -> str:
    return _ensure_timezone(value).strftime("%Y-%m-%d")
