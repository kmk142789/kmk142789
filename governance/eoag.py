"""EOAG operational activation for continuous audit and enforcement."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


STATE_DIR = Path("state/eoag")
LEDGER_PATH = STATE_DIR / "audit_log.jsonl"
REGISTRY_PATH = STATE_DIR / "registry.json"
FINDINGS_PATH = STATE_DIR / "findings.json"
ESCALATIONS_PATH = STATE_DIR / "escalations.json"


@dataclass(slots=True)
class AuditHook:
    """Mandatory audit hook definition for transaction-bearing systems."""

    hook_id: str
    entity: str
    event_type: str
    description: str
    required: bool = True
    audit_gate: bool = True
    evidence_required: bool = True
    settlement_finality_gate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_id": self.hook_id,
            "entity": self.entity,
            "event_type": self.event_type,
            "description": self.description,
            "required": self.required,
            "audit_gate": self.audit_gate,
            "evidence_required": self.evidence_required,
            "settlement_finality_gate": self.settlement_finality_gate,
        }


@dataclass(slots=True)
class IndependencePolicy:
    """Independence and conflict-of-interest controls."""

    separation_of_duties: List[str]
    conflict_checks: List[str]
    recusal_triggers: List[str]
    auditor_rotation_days: int
    external_review_required: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "separation_of_duties": list(self.separation_of_duties),
            "conflict_checks": list(self.conflict_checks),
            "recusal_triggers": list(self.recusal_triggers),
            "auditor_rotation_days": self.auditor_rotation_days,
            "external_review_required": self.external_review_required,
        }


@dataclass(slots=True)
class EvidenceRecord:
    """Immutable evidence entry captured alongside an audit event."""

    evidence_id: str
    artifact: str
    hash: str
    captured_by: str
    captured_at: str
    custody: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "artifact": self.artifact,
            "hash": self.hash,
            "captured_by": self.captured_by,
            "captured_at": self.captured_at,
            "custody": list(self.custody),
        }


@dataclass(slots=True)
class AuditFinding:
    """Audit finding issued by EOAG with corrective actions."""

    finding_id: str
    entity: str
    severity: str
    summary: str
    issued_at: str
    status: str
    corrective_actions: List[Dict[str, Any]] = field(default_factory=list)
    escalations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "entity": self.entity,
            "severity": self.severity,
            "summary": self.summary,
            "issued_at": self.issued_at,
            "status": self.status,
            "corrective_actions": list(self.corrective_actions),
            "escalations": list(self.escalations),
        }


@dataclass(slots=True)
class EscalationRecord:
    """Escalation path when findings require judiciary or enforcement action."""

    escalation_id: str
    target: str
    reason: str
    triggered_at: str
    status: str
    reference: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "target": self.target,
            "reason": self.reason,
            "triggered_at": self.triggered_at,
            "status": self.status,
            "reference": self.reference,
        }


class EOAGRegistry:
    """Registry capturing mandatory audit hooks and independence rules."""

    def __init__(self, hooks: Iterable[AuditHook], independence: IndependencePolicy):
        self.hooks = list(hooks)
        self.independence = independence

    @classmethod
    def default(cls) -> "EOAGRegistry":
        hooks = [
            AuditHook(
                hook_id="dbis-transaction-hook",
                entity="DBIS",
                event_type="transaction",
                description="Capture all DBIS transaction requests and approvals.",
            ),
            AuditHook(
                hook_id="dbis-settlement-hook",
                entity="DBIS",
                event_type="settlement",
                description="Gate DBIS settlement finality on EOAG audit clearance.",
            ),
            AuditHook(
                hook_id="treasury-transaction-hook",
                entity="Treasury",
                event_type="transaction",
                description="Record treasury disbursements, mints, and burns with evidence.",
            ),
            AuditHook(
                hook_id="treasury-settlement-hook",
                entity="Treasury",
                event_type="settlement",
                description="Require EOAG clearance before treasury settlement finality.",
            ),
            AuditHook(
                hook_id="efctia-pre-settlement",
                entity="EFCTIA",
                event_type="pre_settlement",
                description="Log EFCTIA pre-settlement audit checkpoint and approvals.",
            ),
            AuditHook(
                hook_id="efctia-post-settlement",
                entity="EFCTIA",
                event_type="post_settlement",
                description="Capture EFCTIA post-settlement audit and finality receipts.",
            ),
            AuditHook(
                hook_id="governance-decision-hook",
                entity="Governance",
                event_type="governance_decision",
                description="Audit governance decisions, votes, and policy ratifications.",
            ),
            AuditHook(
                hook_id="ecosystem-transaction-hook",
                entity="Ecosystem",
                event_type="transaction",
                description="Ensure all transaction-bearing entities emit EOAG audit hooks.",
            ),
        ]
        independence = IndependencePolicy(
            separation_of_duties=[
                "Auditors cannot approve or execute settlements.",
                "Auditors cannot author the transactions they review.",
                "Audit leads rotate independently of operational leadership.",
            ],
            conflict_checks=[
                "Confirm no shared key custody between auditors and operators.",
                "Validate disclosures for any personal or financial ties.",
                "Enforce dual-control for audit log access and export.",
            ],
            recusal_triggers=[
                "Direct participation in the audited transaction or vote.",
                "Recent employment or advisory role with the audited entity.",
                "Family or financial relationship with transaction beneficiaries.",
            ],
            auditor_rotation_days=90,
            external_review_required=True,
        )
        return cls(hooks=hooks, independence=independence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hooks": [hook.to_dict() for hook in self.hooks],
            "independence": self.independence.to_dict(),
        }

    def save(self, path: Path = REGISTRY_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> "EOAGRegistry":
        if not path.exists():
            registry = cls.default()
            registry.save(path)
            return registry
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        hooks = [AuditHook(**hook) for hook in payload.get("hooks", [])]
        independence = IndependencePolicy(**payload.get("independence", {}))
        return cls(hooks=hooks, independence=independence)


class EOAGAuditLedger:
    """Append-only audit ledger with hash chaining for immutability."""

    def __init__(self, path: Path = LEDGER_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_tail(self) -> tuple[int, str]:
        if not self.path.exists():
            return 0, "GENESIS"
        last_line = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last_line = line
        if not last_line:
            return 0, "GENESIS"
        payload = json.loads(last_line)
        return int(payload.get("sequence", 0)), str(payload.get("hash", "GENESIS"))

    def append_event(
        self,
        entity: str,
        event_type: str,
        action: str,
        details: Dict[str, Any],
        required_clearance: bool,
        evidence: Iterable[EvidenceRecord] | None = None,
    ) -> Dict[str, Any]:
        sequence, previous_hash = self._load_tail()
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "sequence": sequence + 1,
            "event_id": event_id,
            "timestamp": timestamp,
            "entity": entity,
            "event_type": event_type,
            "action": action,
            "details": details,
            "required_clearance": required_clearance,
            "evidence": [record.to_dict() for record in (evidence or [])],
            "previous_hash": previous_hash,
        }
        serialized = json.dumps(payload, sort_keys=True)
        payload["hash"] = sha256(f"{previous_hash}:{serialized}".encode("utf-8")).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        return payload


class EOAGFindings:
    """Track audit findings and corrective actions."""

    def __init__(self, path: Path = FINDINGS_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"findings": []}
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, findings: List[AuditFinding]) -> None:
        payload = {"findings": [finding.to_dict() for finding in findings]}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def issue_finding(
        self,
        entity: str,
        severity: str,
        summary: str,
        corrective_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditFinding:
        issued_at = datetime.now(timezone.utc).isoformat()
        finding = AuditFinding(
            finding_id=str(uuid.uuid4()),
            entity=entity,
            severity=severity,
            summary=summary,
            issued_at=issued_at,
            status="open",
            corrective_actions=corrective_actions or [],
        )
        data = self.load()
        findings = [AuditFinding(**item) for item in data.get("findings", [])]
        findings.append(finding)
        self.save(findings)
        return finding


class EOAGEscalations:
    """Record judiciary or enforcement escalations."""

    def __init__(self, path: Path = ESCALATIONS_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"escalations": []}
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, escalations: List[EscalationRecord]) -> None:
        payload = {"escalations": [record.to_dict() for record in escalations]}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def record(self, target: str, reason: str, reference: Optional[str] = None) -> EscalationRecord:
        record = EscalationRecord(
            escalation_id=str(uuid.uuid4()),
            target=target,
            reason=reason,
            triggered_at=datetime.now(timezone.utc).isoformat(),
            status="pending",
            reference=reference,
        )
        payload = self.load()
        escalations = [EscalationRecord(**item) for item in payload.get("escalations", [])]
        escalations.append(record)
        self.save(escalations)
        return record


class EOAGContinuousAudit:
    """Continuous audit interface for transaction-bearing entities."""

    def __init__(self) -> None:
        self.registry = EOAGRegistry.load()
        self.ledger = EOAGAuditLedger()
        self.findings = EOAGFindings()
        self.escalations = EOAGEscalations()

    def record_event(
        self,
        entity: str,
        event_type: str,
        action: str,
        details: Dict[str, Any],
        required_clearance: bool = True,
        evidence: Iterable[EvidenceRecord] | None = None,
    ) -> Dict[str, Any]:
        return self.ledger.append_event(
            entity=entity,
            event_type=event_type,
            action=action,
            details=details,
            required_clearance=required_clearance,
            evidence=evidence,
        )

    def require_audit_clearance(self, entity: str, event_type: str) -> bool:
        for hook in self.registry.hooks:
            if hook.entity == entity and hook.event_type == event_type:
                return hook.audit_gate
        return False

    def issue_finding(
        self,
        entity: str,
        severity: str,
        summary: str,
        corrective_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditFinding:
        return self.findings.issue_finding(entity, severity, summary, corrective_actions)

    def escalate(self, target: str, reason: str, reference: Optional[str] = None) -> EscalationRecord:
        return self.escalations.record(target=target, reason=reason, reference=reference)


def bootstrap_eoag_state() -> Dict[str, Any]:
    """Initialize EOAG state with default registry and activation entries."""

    registry = EOAGRegistry.default()
    registry.save()

    ledger = EOAGAuditLedger()
    ledger.append_event(
        entity="EOAG",
        event_type="activation",
        action="bootstrap",
        details={
            "message": "EOAG activated with continuous audit hooks.",
            "hooks_registered": [hook.hook_id for hook in registry.hooks],
        },
        required_clearance=False,
        evidence=[],
    )

    findings = EOAGFindings()
    findings.save([])

    escalations = EOAGEscalations()
    escalations.save([])

    return {
        "registry": registry.to_dict(),
        "ledger_path": str(LEDGER_PATH),
        "findings_path": str(FINDINGS_PATH),
        "escalations_path": str(ESCALATIONS_PATH),
    }
