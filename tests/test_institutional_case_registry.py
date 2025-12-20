"""Tests for institutional case registry schema and helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from echo.schemas.institutional_case_registry import (
    CaseEvent,
    CasePriority,
    CaseStatus,
    CaseStateMachine,
    ContactInfo,
    EngagementEdge,
    EngagementMap,
    ExternalIntake,
    InstitutionRecord,
    ReferenceRegistryEntry,
    build_case_registry,
    has_permission,
)


def _build_registry_payload():
    now = datetime.now(timezone.utc)
    intake = ExternalIntake(
        intake_id="intake-0001",
        submitted_at=now - timedelta(days=4),
        channel="email",
        summary="Request support for cross-agency coordination.",
        requested_by=ContactInfo(name="Ari Quinn", organization="Echo Civic Lab"),
        source_url="https://echo.example.org/intake/0001",
        attachments=["intake_form.pdf"],
    )
    events = [
        CaseEvent(
            event_id="event-001",
            timestamp=now - timedelta(days=3),
            actor="case.bot",
            action="triage",
            status=CaseStatus.triaged,
            notes="Initial assessment completed.",
        ),
        CaseEvent(
            event_id="event-002",
            timestamp=now - timedelta(days=1),
            actor="case.manager",
            action="assign",
            status=CaseStatus.in_progress,
            notes="Assigned to engagement team.",
        ),
    ]
    case = {
        "case_id": "case-001",
        "title": "Civic coordination intake",
        "status": CaseStatus.in_progress,
        "priority": CasePriority.high,
        "intake": intake,
        "assigned_team": "engagement",
        "tags": ["coordination", "multi-agency"],
        "events": events,
        "evidence_refs": ["ledger://cases/001"],
        "updated_at": now,
    }
    institutions = [
        InstitutionRecord(
            institution_id="inst-001",
            name="Echo Civic Lab",
            sector="public interest",
            region="North America",
            primary_contact=ContactInfo(name="Ari Quinn", email="ari@example.org"),
        ),
        InstitutionRecord(
            institution_id="inst-002",
            name="Harmony Council",
            sector="governance",
            region="Global",
            primary_contact=ContactInfo(name="Sam Rowe", email="sam@example.org"),
        ),
    ]
    engagements = [
        EngagementEdge(
            source_institution_id="inst-001",
            target_institution_id="inst-002",
            relationship="coordination",
            status="active",
            last_contacted_at=now - timedelta(days=2),
        )
    ]
    engagement_map = EngagementMap(institutions=institutions, engagements=engagements)
    references = [
        ReferenceRegistryEntry(
            reference_id="ref-001",
            system="Echo Ledger",
            url="https://ledger.example.org/cases/001",
            description="Immutable ledger entry for case evidence.",
        )
    ]
    registry = build_case_registry(
        registry_id="institutional-case-registry",
        version="1.0",
        cases=[case],
        engagement_map=engagement_map,
        reference_registry=references,
    )
    return registry


def test_case_registry_dashboard_metrics() -> None:
    registry = _build_registry_payload()

    assert registry.dashboard.total_cases == 1
    assert registry.dashboard.open_cases == 1
    assert registry.dashboard.cases_by_status[CaseStatus.in_progress] == 1
    assert registry.dashboard.cases_by_priority[CasePriority.high] == 1
    assert registry.dashboard.oldest_open_case_days is not None
    assert registry.dashboard.latest_intake_at is not None


def test_case_registry_schema_matches_json_schema() -> None:
    registry = _build_registry_payload()
    payload = registry.to_machine_registry()

    schema_path = Path("schemas/institutional_case_registry.schema.json")
    schema = json.loads(schema_path.read_text())

    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(instance=payload, schema=schema)


def test_role_permission_check() -> None:
    registry = _build_registry_payload()

    assert has_permission("case_manager", "case:update", registry.roles) is True
    assert has_permission("analyst", "case:close", registry.roles) is False


def test_case_event_status_mismatch_raises() -> None:
    now = datetime.now(timezone.utc)
    intake = ExternalIntake(
        intake_id="intake-0002",
        submitted_at=now,
        channel="web",
        summary="Portal submission",
        requested_by=ContactInfo(name="Taylor")
    )
    with pytest.raises(ValueError):
        build_case_registry(
            registry_id="registry",
            version="1.0",
            cases=[
                {
                    "case_id": "case-002",
                    "title": "Mismatch",
                    "status": CaseStatus.triaged,
                    "priority": CasePriority.medium,
                    "intake": intake,
                    "events": [
                        CaseEvent(
                            event_id="event-003",
                            timestamp=now,
                            actor="case.bot",
                            action="triage",
                            status=CaseStatus.in_progress,
                        )
                    ],
                    "updated_at": now,
                }
            ],
            engagement_map=EngagementMap(institutions=[], engagements=[]),
        )


def test_case_state_machine_transition_appends_ledger() -> None:
    registry = _build_registry_payload()
    case = registry.cases[0]
    machine = CaseStateMachine()

    updated = machine.transition_case(
        case,
        to_status=CaseStatus.resolved,
        actor="case.manager",
        role="case_manager",
        reason="Work completed",
        decision_id="decision-001",
        decision_version="1.0.0",
    )

    assert updated.status == CaseStatus.resolved
    assert updated.transition_ledger[-1].from_status == CaseStatus.in_progress
    assert updated.transition_ledger[-1].to_status == CaseStatus.resolved
    assert updated.events[-1].status == CaseStatus.resolved


def test_case_state_machine_permissions_enforced() -> None:
    registry = _build_registry_payload()
    case = registry.cases[0]
    machine = CaseStateMachine()

    with pytest.raises(PermissionError):
        machine.transition_case(
            case,
            to_status=CaseStatus.resolved,
            actor="case.analyst",
            role="analyst",
            reason="Attempted transition",
            decision_id="decision-002",
            decision_version="1.0.0",
        )

    with pytest.raises(ValueError):
        machine.transition_case(
            case,
            to_status=CaseStatus.new,
            actor="case.manager",
            role="case_manager",
            reason="Invalid transition",
        )


def test_case_resolution_requires_decision_reference() -> None:
    registry = _build_registry_payload()
    case = registry.cases[0]
    machine = CaseStateMachine()

    with pytest.raises(ValueError):
        machine.transition_case(
            case,
            to_status=CaseStatus.resolved,
            actor="case.manager",
            role="case_manager",
            reason="Missing decision",
        )
