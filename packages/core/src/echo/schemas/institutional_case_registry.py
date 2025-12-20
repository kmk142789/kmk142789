"""Schema and helpers for institutional case tracking registries."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional, Set

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "IntakeChannel",
    "CaseStatus",
    "CasePriority",
    "ContactInfo",
    "ExternalIntake",
    "CaseEvent",
    "CaseTransition",
    "CaseRecord",
    "InstitutionRecord",
    "EngagementEdge",
    "EngagementMap",
    "ReferenceRegistryEntry",
    "OperationalDashboard",
    "CaseRegistry",
    "CaseStateMachine",
    "DEFAULT_CASE_TRANSITIONS",
    "DEFAULT_ROLE_PERMISSIONS",
    "build_operational_dashboard",
    "build_case_registry",
    "has_permission",
    "transition_permission_key",
]


class IntakeChannel(str, Enum):
    """External intake channels for case creation."""

    email = "email"
    web = "web"
    phone = "phone"
    referral = "referral"
    other = "other"


class CaseStatus(str, Enum):
    """Lifecycle states for a tracked case."""

    new = "new"
    triaged = "triaged"
    in_review = "in_review"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class CasePriority(str, Enum):
    """Priority tier for operational escalation."""

    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ContactInfo(BaseModel):
    """Contact details for external requests and institutional stakeholders."""

    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None


class ExternalIntake(BaseModel):
    """Structured intake record originating outside the system."""

    intake_id: str = Field(..., min_length=1)
    submitted_at: datetime = Field(..., description="Timestamp of intake submission")
    channel: IntakeChannel
    summary: str = Field(..., min_length=1)
    requested_by: ContactInfo
    source_url: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class CaseEvent(BaseModel):
    """Event capturing a meaningful state change or note."""

    event_id: str = Field(..., min_length=1)
    timestamp: datetime
    actor: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    status: Optional[CaseStatus] = None
    notes: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class CaseTransition(BaseModel):
    """Immutable ledger entry describing a case state transition."""

    transition_id: str = Field(..., min_length=1)
    timestamp: datetime
    actor: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    from_status: CaseStatus
    to_status: CaseStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class CaseRecord(BaseModel):
    """Primary record for structured case tracking."""

    case_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    status: CaseStatus
    priority: CasePriority
    intake: ExternalIntake
    assigned_team: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    events: List[CaseEvent] = Field(default_factory=list)
    transition_ledger: List[CaseTransition] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _ensure_latest_status(self) -> "CaseRecord":
        if self.events:
            ordered = sorted(self.events, key=lambda event: event.timestamp)
            latest = ordered[-1]
            if latest.status and latest.status != self.status:
                raise ValueError("latest event status must match case status")
            if latest.timestamp > self.updated_at:
                raise ValueError("updated_at must be on or after latest event timestamp")
        if self.transition_ledger:
            ordered = sorted(self.transition_ledger, key=lambda entry: entry.timestamp)
            if ordered != self.transition_ledger:
                raise ValueError("transition ledger must be ordered by timestamp")
            if len({entry.transition_id for entry in ordered}) != len(ordered):
                raise ValueError("transition_id must be unique within transition ledger")
            for idx, entry in enumerate(ordered[1:], start=1):
                previous = ordered[idx - 1]
                if entry.from_status != previous.to_status:
                    raise ValueError("transition ledger must form a contiguous chain")
            if ordered[-1].to_status != self.status:
                raise ValueError("latest transition must match case status")
            if ordered[-1].timestamp > self.updated_at:
                raise ValueError("updated_at must be on or after latest transition timestamp")
        return self


class InstitutionRecord(BaseModel):
    """Registry entry describing an engaged institution."""

    institution_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sector: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    primary_contact: Optional[ContactInfo] = None
    notes: Optional[str] = None


class EngagementEdge(BaseModel):
    """Connection between institutions describing collaboration."""

    source_institution_id: str = Field(..., min_length=1)
    target_institution_id: str = Field(..., min_length=1)
    relationship: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    last_contacted_at: Optional[datetime] = None


class EngagementMap(BaseModel):
    """Map of institutional engagement relationships."""

    institutions: List[InstitutionRecord] = Field(default_factory=list)
    engagements: List[EngagementEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_engagements(self) -> "EngagementMap":
        valid_ids = {institution.institution_id for institution in self.institutions}
        for engagement in self.engagements:
            if engagement.source_institution_id not in valid_ids:
                raise ValueError("engagement source must exist in institution registry")
            if engagement.target_institution_id not in valid_ids:
                raise ValueError("engagement target must exist in institution registry")
        return self


class ReferenceRegistryEntry(BaseModel):
    """Reference registry entry for external systems or internal ledgers."""

    reference_id: str = Field(..., min_length=1)
    system: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class OperationalDashboard(BaseModel):
    """Aggregated operational metrics for the registry dashboard."""

    generated_at: datetime
    total_cases: int = Field(..., ge=0)
    open_cases: int = Field(..., ge=0)
    cases_by_status: Dict[CaseStatus, int]
    cases_by_priority: Dict[CasePriority, int]
    oldest_open_case_days: Optional[int] = Field(default=None, ge=0)
    latest_intake_at: Optional[datetime] = None


class CaseRegistry(BaseModel):
    """Machine-readable registry containing cases, engagement maps, and dashboards."""

    registry_id: str = Field(..., min_length=1)
    generated_at: datetime
    version: str = Field(..., min_length=1)
    cases: List[CaseRecord]
    engagement_map: EngagementMap
    roles: Dict[str, Dict[str, List[str]]]
    reference_registry: List[ReferenceRegistryEntry]
    dashboard: OperationalDashboard

    def to_machine_registry(self) -> Dict[str, object]:
        """Return a JSON-ready dictionary representation."""

        return self.model_dump(mode="json")


DEFAULT_ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    "intake_coordinator": {
        "description": ["Create intake records and initial case summaries."],
        "permissions": [
            "intake:create",
            "intake:triage",
            "case:transition:new:triaged",
        ],
    },
    "case_manager": {
        "description": ["Manage case lifecycles and stakeholder communication."],
        "permissions": [
            "case:update",
            "case:assign",
            "case:close",
            "case:transition:triaged:in_review",
            "case:transition:triaged:in_progress",
            "case:transition:in_review:in_progress",
            "case:transition:in_review:resolved",
            "case:transition:in_progress:resolved",
            "case:transition:resolved:closed",
            "case:transition:resolved:in_progress",
        ],
    },
    "analyst": {
        "description": ["Read registry data and build operational reports."],
        "permissions": ["registry:read", "dashboard:read"],
    },
    "engagement_lead": {
        "description": ["Maintain institutional engagement relationships."],
        "permissions": ["engagement:update", "engagement:map"],
    },
}


def has_permission(role: str, action: str, permissions: Mapping[str, Mapping[str, List[str]]]) -> bool:
    """Check whether a role grants a specific permission action."""

    role_permissions = permissions.get(role, {}).get("permissions", [])
    return action in role_permissions


DEFAULT_CASE_TRANSITIONS: Dict[CaseStatus, Set[CaseStatus]] = {
    CaseStatus.new: {CaseStatus.triaged},
    CaseStatus.triaged: {CaseStatus.in_review, CaseStatus.in_progress},
    CaseStatus.in_review: {CaseStatus.in_progress, CaseStatus.resolved},
    CaseStatus.in_progress: {CaseStatus.resolved},
    CaseStatus.resolved: {CaseStatus.closed, CaseStatus.in_progress},
    CaseStatus.closed: set(),
}


def transition_permission_key(from_status: CaseStatus, to_status: CaseStatus) -> str:
    """Return the permission key required for a specific transition."""

    return f"case:transition:{from_status.value}:{to_status.value}"


class CaseStateMachine:
    """Enforced case state machine with role-based transition permissions."""

    def __init__(
        self,
        *,
        transitions: Mapping[CaseStatus, Iterable[CaseStatus]] = DEFAULT_CASE_TRANSITIONS,
        role_permissions: Mapping[str, Mapping[str, List[str]]] = DEFAULT_ROLE_PERMISSIONS,
    ) -> None:
        self._transitions = {status: set(next_states) for status, next_states in transitions.items()}
        self._role_permissions = role_permissions

    def allowed_transitions(self, status: CaseStatus) -> Set[CaseStatus]:
        """Return allowed transitions for a status."""

        return set(self._transitions.get(status, set()))

    def transition_case(
        self,
        case: CaseRecord,
        *,
        to_status: CaseStatus,
        actor: str,
        role: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
        transition_id: Optional[str] = None,
        event_id: Optional[str] = None,
        action: str = "status-transition",
    ) -> CaseRecord:
        """Transition a case and append an immutable ledger entry."""

        from_status = case.status
        if to_status not in self.allowed_transitions(from_status):
            raise ValueError(f"invalid transition from {from_status.value} to {to_status.value}")
        permission = transition_permission_key(from_status, to_status)
        if not has_permission(role, permission, self._role_permissions):
            raise PermissionError(f"role {role} lacks permission {permission}")

        now = timestamp or datetime.now(timezone.utc)
        transition_id = transition_id or f"{case.case_id}-transition-{len(case.transition_ledger) + 1}"
        metadata = dict(metadata or {})
        ledger_entry = CaseTransition(
            transition_id=transition_id,
            timestamp=now,
            actor=actor,
            role=role,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            notes=notes,
            metadata=metadata,
        )
        event_id = event_id or f"{transition_id}-event"
        event_notes = notes or reason
        event = CaseEvent(
            event_id=event_id,
            timestamp=now,
            actor=actor,
            action=action,
            status=to_status,
            notes=event_notes,
            metadata=metadata,
        )
        events = list(case.events)
        events.append(event)
        ledger = list(case.transition_ledger)
        ledger.append(ledger_entry)
        return case.model_copy(
            update={
                "status": to_status,
                "events": events,
                "transition_ledger": ledger,
                "updated_at": now,
            }
        )


def build_operational_dashboard(cases: Iterable[CaseRecord]) -> OperationalDashboard:
    """Aggregate case metrics for operational dashboards."""

    cases = list(cases)
    now = datetime.now(timezone.utc)
    status_counts = {status: 0 for status in CaseStatus}
    priority_counts = {priority: 0 for priority in CasePriority}
    open_statuses = {CaseStatus.new, CaseStatus.triaged, CaseStatus.in_review, CaseStatus.in_progress}

    oldest_open_days: Optional[int] = None
    latest_intake_at: Optional[datetime] = None

    for case in cases:
        status_counts[case.status] += 1
        priority_counts[case.priority] += 1
        if case.status in open_statuses:
            age_days = max(0, int((now - case.intake.submitted_at).days))
            oldest_open_days = age_days if oldest_open_days is None else max(oldest_open_days, age_days)
        if latest_intake_at is None or case.intake.submitted_at > latest_intake_at:
            latest_intake_at = case.intake.submitted_at

    open_cases = sum(status_counts[status] for status in open_statuses)

    return OperationalDashboard(
        generated_at=now,
        total_cases=len(cases),
        open_cases=open_cases,
        cases_by_status=status_counts,
        cases_by_priority=priority_counts,
        oldest_open_case_days=oldest_open_days,
        latest_intake_at=latest_intake_at,
    )


def build_case_registry(
    *,
    registry_id: str,
    version: str,
    cases: Iterable[CaseRecord],
    engagement_map: EngagementMap,
    roles: Optional[Dict[str, Dict[str, List[str]]]] = None,
    reference_registry: Optional[Iterable[ReferenceRegistryEntry]] = None,
) -> CaseRegistry:
    """Build a complete registry payload with a computed dashboard."""

    cases_list = [
        case if isinstance(case, CaseRecord) else CaseRecord.model_validate(case)
        for case in cases
    ]
    dashboard = build_operational_dashboard(cases_list)
    return CaseRegistry(
        registry_id=registry_id,
        generated_at=dashboard.generated_at,
        version=version,
        cases=cases_list,
        engagement_map=engagement_map,
        roles=roles or dict(DEFAULT_ROLE_PERMISSIONS),
        reference_registry=list(reference_registry or []),
        dashboard=dashboard,
    )
