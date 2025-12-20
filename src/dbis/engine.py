"""Core transaction engine for the Echo Digital Bank of International Settlements."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


class Rail(str, Enum):
    FIAT = "fiat"
    CBDC = "cbdc"
    STABLECOIN = "stablecoin"
    TOKENIZED_ASSET = "tokenized_asset"
    OFFCHAIN_INSTRUMENT = "offchain_instrument"


@dataclass(frozen=True)
class PartyIdentity:
    """Identity bindings required for DBIS actions."""

    identity_id: str
    legal_name: str
    did: str
    dns_record: str
    roles: tuple[str, ...] = ()
    attestation_refs: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.identity_id:
            issues.append("missing_identity_id")
        if not self.did:
            issues.append("missing_did")
        if not self.dns_record:
            issues.append("missing_dns_record")
        if not self.attestation_refs:
            issues.append("missing_attestation_refs")
        return issues


@dataclass(frozen=True)
class ComplianceProfile:
    aml_risk_score: float
    sanctions_status: str
    dispute_window_days: int
    rollback_policy: str
    jurisdiction: str
    kyc_tier: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "aml_risk_score": self.aml_risk_score,
            "sanctions_status": self.sanctions_status,
            "dispute_window_days": self.dispute_window_days,
            "rollback_policy": self.rollback_policy,
            "jurisdiction": self.jurisdiction,
            "kyc_tier": self.kyc_tier,
        }


@dataclass
class TransactionIntent:
    intent_id: str
    amount: float
    currency: str
    rail: Rail
    sender: PartyIdentity
    receiver: PartyIdentity
    memo: str
    governance_ref: str
    approvals: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: _now_iso())
    status: str = "PENDING"

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "amount": self.amount,
            "currency": self.currency,
            "rail": self.rail.value,
            "sender": _identity_payload(self.sender),
            "receiver": _identity_payload(self.receiver),
            "memo": self.memo,
            "governance_ref": self.governance_ref,
            "approvals": list(self.approvals),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "status": self.status,
        }


@dataclass
class TransactionBatch:
    batch_id: str
    intents: list[TransactionIntent]
    offline: bool
    created_at: str = field(default_factory=lambda: _now_iso())
    signatures: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "offline": self.offline,
            "created_at": self.created_at,
            "signatures": list(self.signatures),
            "intents": [intent.as_dict() for intent in self.intents],
        }


@dataclass(frozen=True)
class SettlementReceipt:
    settlement_id: str
    intent_id: str
    amount: float
    currency: str
    rail: Rail
    settled_at: str
    finality_hash: str
    ledger_hash: str
    governance_ref: str
    compliance_snapshot: dict[str, Any]
    audit_hooks: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "settlement_id": self.settlement_id,
            "intent_id": self.intent_id,
            "amount": self.amount,
            "currency": self.currency,
            "rail": self.rail.value,
            "settled_at": self.settled_at,
            "finality_hash": self.finality_hash,
            "ledger_hash": self.ledger_hash,
            "governance_ref": self.governance_ref,
            "compliance_snapshot": self.compliance_snapshot,
            "audit_hooks": list(self.audit_hooks),
        }


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    actor: str
    timestamp: str
    intent_id: str | None
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "intent_id": self.intent_id,
            "details": self.details,
        }


@dataclass(frozen=True)
class AttestationRecord:
    attestation_id: str
    intent_id: str
    ledger_hash: str
    governance_ref: str
    subject_identity: dict[str, Any]
    dns_binding: str
    issued_at: str
    signatures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "intent_id": self.intent_id,
            "ledger_hash": self.ledger_hash,
            "governance_ref": self.governance_ref,
            "subject_identity": self.subject_identity,
            "dns_binding": self.dns_binding,
            "issued_at": self.issued_at,
            "signatures": list(self.signatures),
        }


class DbisLedger:
    """Append-only JSONL ledger with hash chaining."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, entry_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self._last_hash()
        entry = {
            "seq": self._count_entries() + 1,
            "entry_type": entry_type,
            "timestamp": _now_iso(),
            "payload": payload,
            "prev_hash": existing,
        }
        entry_hash = _hash_payload(entry)
        entry["hash"] = entry_hash
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json_dumps(entry) + "\n")
        return entry

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json_loads(line))
        return rows

    def _count_entries(self) -> int:
        return len(self.entries())

    def _last_hash(self) -> str | None:
        entries = self.entries()
        if not entries:
            return None
        return entries[-1].get("hash")


class DbisEngine:
    """DBIS transaction coordination engine."""

    def __init__(self, state_dir: Path | str = "state/dbis") -> None:
        self.state_dir = Path(state_dir)
        self.transaction_ledger = DbisLedger(self.state_dir / "transaction_ledger.jsonl")
        self.audit_ledger = DbisLedger(self.state_dir / "audit_log.jsonl")
        self.reconciliation_ledger = DbisLedger(self.state_dir / "reconciliation_log.jsonl")

    def create_intent(
        self,
        *,
        amount: float,
        currency: str,
        rail: Rail,
        sender: PartyIdentity,
        receiver: PartyIdentity,
        memo: str,
        governance_ref: str,
        approvals: Iterable[str] = (),
        metadata: dict[str, Any] | None = None,
    ) -> TransactionIntent:
        return TransactionIntent(
            intent_id=str(uuid4()),
            amount=amount,
            currency=currency,
            rail=rail,
            sender=sender,
            receiver=receiver,
            memo=memo,
            governance_ref=governance_ref,
            approvals=tuple(approvals),
            metadata=metadata or {},
        )

    def validate_intent(
        self, intent: TransactionIntent, compliance: ComplianceProfile
    ) -> list[str]:
        issues = []
        issues.extend(intent.sender.validate())
        issues.extend(intent.receiver.validate())
        if compliance.aml_risk_score > 0.8:
            issues.append("aml_risk_score_exceeds_threshold")
        if compliance.sanctions_status.lower() != "clear":
            issues.append("sanctions_flagged")
        if not intent.governance_ref:
            issues.append("missing_governance_ref")
        if intent.amount <= 0:
            issues.append("invalid_amount")
        return issues

    def settle_intent(
        self,
        intent: TransactionIntent,
        compliance: ComplianceProfile,
        *,
        actor: str,
        audit_hooks: Iterable[str] = (),
        status: str = "SETTLED",
    ) -> SettlementReceipt:
        issues = self.validate_intent(intent, compliance)
        if issues:
            raise ValueError(f"intent invalid: {issues}")
        intent.status = status
        intent_payload = intent.as_dict()
        ledger_entry = self.transaction_ledger.append("transaction_intent", intent_payload)
        finality_hash = _hash_payload(
            {
                "intent": intent_payload,
                "ledger_hash": ledger_entry["hash"],
                "compliance": compliance.as_dict(),
            }
        )
        receipt = SettlementReceipt(
            settlement_id=str(uuid4()),
            intent_id=intent.intent_id,
            amount=intent.amount,
            currency=intent.currency,
            rail=intent.rail,
            settled_at=_now_iso(),
            finality_hash=finality_hash,
            ledger_hash=ledger_entry["hash"],
            governance_ref=intent.governance_ref,
            compliance_snapshot=compliance.as_dict(),
            audit_hooks=tuple(audit_hooks),
        )
        self.transaction_ledger.append("settlement_receipt", receipt.as_dict())
        self.audit_ledger.append(
            "audit_event",
            self._audit_event(
                event_type="SETTLEMENT_FINALIZED",
                actor=actor,
                intent_id=intent.intent_id,
                details={
                    "settlement_id": receipt.settlement_id,
                    "finality_hash": receipt.finality_hash,
                    "audit_hooks": list(audit_hooks),
                },
            ).as_dict(),
        )
        return receipt

    def stage_offline_batch(
        self,
        intents: Iterable[TransactionIntent],
        *,
        signatures: Iterable[str],
        actor: str,
    ) -> TransactionBatch:
        batch = TransactionBatch(
            batch_id=str(uuid4()),
            intents=list(intents),
            offline=True,
            signatures=tuple(signatures),
        )
        self.audit_ledger.append(
            "audit_event",
            self._audit_event(
                event_type="OFFLINE_BATCH_STAGED",
                actor=actor,
                intent_id=None,
                details=batch.as_dict(),
            ).as_dict(),
        )
        for intent in batch.intents:
            intent.status = "STAGED"
            self.transaction_ledger.append("offline_intent", intent.as_dict())
        return batch

    def finalize_offline_batch(
        self,
        batch: TransactionBatch,
        compliance: ComplianceProfile,
        *,
        verifier: str,
        verification_notes: str,
        audit_hooks: Iterable[str] = (),
    ) -> list[SettlementReceipt]:
        receipts = []
        self.audit_ledger.append(
            "audit_event",
            self._audit_event(
                event_type="OFFLINE_BATCH_VERIFIED",
                actor=verifier,
                intent_id=None,
                details={
                    "batch_id": batch.batch_id,
                    "verification_notes": verification_notes,
                },
            ).as_dict(),
        )
        for intent in batch.intents:
            receipt = self.settle_intent(
                intent,
                compliance,
                actor=verifier,
                audit_hooks=audit_hooks,
                status="SETTLED_DELAYED",
            )
            receipts.append(receipt)
        return receipts

    def record_attestation(
        self,
        intent: TransactionIntent,
        *,
        ledger_hash: str,
        governance_ref: str,
        signatures: Iterable[str],
    ) -> AttestationRecord:
        record = AttestationRecord(
            attestation_id=str(uuid4()),
            intent_id=intent.intent_id,
            ledger_hash=ledger_hash,
            governance_ref=governance_ref,
            subject_identity=_identity_payload(intent.sender),
            dns_binding=intent.sender.dns_record,
            issued_at=_now_iso(),
            signatures=tuple(signatures),
        )
        self.audit_ledger.append("attestation", record.as_dict())
        return record

    def generate_scorecard(self) -> dict[str, Any]:
        entries = self.transaction_ledger.entries()
        receipts = [e for e in entries if e.get("entry_type") == "settlement_receipt"]
        total_value = sum(r["payload"]["amount"] for r in receipts)
        rails: dict[str, int] = {}
        for receipt in receipts:
            rail = receipt["payload"]["rail"]
            rails[rail] = rails.get(rail, 0) + 1
        return {
            "generated_at": _now_iso(),
            "total_settled_value": total_value,
            "settlement_count": len(receipts),
            "rail_mix": rails,
        }

    def generate_transparency_report(self) -> dict[str, Any]:
        return {
            "generated_at": _now_iso(),
            "scorecard": self.generate_scorecard(),
            "audit_events": len(self.audit_ledger.entries()),
            "reconciliation_events": len(self.reconciliation_ledger.entries()),
        }

    def reconcile(self, *, actor: str, notes: str) -> dict[str, Any]:
        payload = {
            "actor": actor,
            "notes": notes,
            "ledger_tip": self.transaction_ledger._last_hash(),
            "audit_tip": self.audit_ledger._last_hash(),
        }
        entry = self.reconciliation_ledger.append("reconciliation", payload)
        return entry

    def _audit_event(
        self,
        *,
        event_type: str,
        actor: str,
        intent_id: str | None,
        details: dict[str, Any],
    ) -> AuditEvent:
        return AuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            actor=actor,
            timestamp=_now_iso(),
            intent_id=intent_id,
            details=details,
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(payload: dict[str, Any]) -> str:
    return sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def _identity_payload(identity: PartyIdentity) -> dict[str, Any]:
    return {
        "identity_id": identity.identity_id,
        "legal_name": identity.legal_name,
        "did": identity.did,
        "dns_record": identity.dns_record,
        "roles": list(identity.roles),
        "attestation_refs": list(identity.attestation_refs),
    }


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def json_loads(payload: str) -> dict[str, Any]:
    import json

    return json.loads(payload)


__all__ = [
    "AttestationRecord",
    "AuditEvent",
    "ComplianceProfile",
    "DbisEngine",
    "DbisLedger",
    "PartyIdentity",
    "Rail",
    "SettlementReceipt",
    "TransactionBatch",
    "TransactionIntent",
]
