"""EFCTIA transaction integrity validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Iterable, List, Optional

from pydantic import BaseModel, Field


class TransactionState(str, Enum):
    PROPOSED = "proposed"
    AUTHORIZED = "authorized"
    SETTLED = "settled"
    DISPUTED = "disputed"
    REVERSED = "reversed"
    FINALIZED = "finalized"


class ComplianceTier(str, Enum):
    HUMANITARIAN = "humanitarian"
    PUBLIC_SERVICE = "public_service"
    COMMERCIAL = "commercial"
    SOVEREIGN = "sovereign"


class IdentityBinding(BaseModel):
    identity_id: str
    authority: str
    assurance_level: str


class AuthorizationStep(BaseModel):
    actor: str
    action: str
    timestamp: datetime
    attestation_ref: Optional[str] = None


class ProvenanceRecord(BaseModel):
    source_system: str
    reference: str
    checksum: str


class PurposeDeclaration(BaseModel):
    category: str
    description: str


class ComplianceMetadata(BaseModel):
    tier: ComplianceTier
    aml_program: str
    sanctions_signal: str
    risk_rating: str
    sealed_reference: str
    public_summary: str


class IntegrityAttestation(BaseModel):
    attestation_id: str
    attestation_type: str
    signer: str
    signature_ref: str


class DisputeReference(BaseModel):
    case_id: str
    tribunal: str
    issued_by: str
    reason: str


class TransactionPayload(BaseModel):
    transaction_id: str
    state: TransactionState
    amount: Decimal = Field(..., gt=0)
    asset: str
    origin_institution: str
    destination_institution: str
    cross_institution: bool
    proposed_at: datetime
    authorized_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    dns_substrate_ref: str
    governance_kernel_ref: str
    identity_binding: IdentityBinding
    provenance: List[ProvenanceRecord]
    authorization_chain: List[AuthorizationStep]
    purpose: PurposeDeclaration
    compliance: ComplianceMetadata
    attestation: Optional[IntegrityAttestation] = None
    dispute_reference: Optional[DisputeReference] = None
    enforcement_actions: List[str] = Field(default_factory=list)


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class IntegrityCheckResult:
    issues: List[IntegrityIssue]

    @property
    def is_valid(self) -> bool:
        return not self.issues


class TransactionIntegrityValidator:
    """Validate EFCTIA transaction integrity constraints."""

    def __init__(self, *, high_value_threshold: Decimal = Decimal("1000000")) -> None:
        self.high_value_threshold = high_value_threshold
        self.required_identity_authorities = {"ECIA", "Echo Citizenship & Identity Authority (ECIA)"}

    def validate(self, payload: TransactionPayload) -> IntegrityCheckResult:
        issues: list[IntegrityIssue] = []
        is_high_value = payload.amount >= self.high_value_threshold

        if not payload.provenance:
            issues.append(
                IntegrityIssue(
                    code="missing_provenance",
                    message="Provenance records are required for integrity validation.",
                )
            )

        if payload.state in {TransactionState.AUTHORIZED, TransactionState.SETTLED}:
            if not payload.authorization_chain:
                issues.append(
                    IntegrityIssue(
                        code="missing_authorization_chain",
                        message="Authorization chain required for authorized or settled states.",
                    )
                )

        if payload.state in {TransactionState.DISPUTED, TransactionState.REVERSED}:
            if payload.dispute_reference is None:
                issues.append(
                    IntegrityIssue(
                        code="missing_dispute_reference",
                        message="Dispute reference required for disputed or reversed states.",
                    )
                )

        if payload.state == TransactionState.REVERSED and not payload.enforcement_actions:
            issues.append(
                IntegrityIssue(
                    code="missing_enforcement_actions",
                    message="Reversed transactions must log enforcement actions.",
                )
            )

        if payload.cross_institution or is_high_value:
            if payload.attestation is None:
                issues.append(
                    IntegrityIssue(
                        code="missing_attestation",
                        message="High-value or cross-institution transfers require attestation.",
                    )
                )

        if not payload.dns_substrate_ref:
            issues.append(
                IntegrityIssue(
                    code="missing_dns_binding",
                    message="DNS substrate reference is mandatory for EFCTIA binding.",
                )
            )

        if not payload.governance_kernel_ref:
            issues.append(
                IntegrityIssue(
                    code="missing_governance_binding",
                    message="Governance kernel reference is mandatory for EFCTIA binding.",
                )
            )

        if payload.identity_binding.authority not in self.required_identity_authorities:
            issues.append(
                IntegrityIssue(
                    code="invalid_identity_authority",
                    message="ECIA identity authority is required for EFCTIA integrity validation.",
                )
            )

        if not payload.compliance.sealed_reference:
            issues.append(
                IntegrityIssue(
                    code="missing_sealed_reference",
                    message="Compliance metadata must include sealed references.",
                )
            )

        if not payload.compliance.public_summary:
            issues.append(
                IntegrityIssue(
                    code="missing_public_summary",
                    message="Compliance metadata must include a public summary.",
                )
            )

        return IntegrityCheckResult(issues=issues)


def audit_pre_settlement(payload: TransactionPayload) -> IntegrityCheckResult:
    """Run EFCTIA pre-settlement integrity audit."""

    validator = TransactionIntegrityValidator()
    result = validator.validate(payload)
    if payload.state != TransactionState.AUTHORIZED:
        issues = result.issues + [
            IntegrityIssue(
                code="invalid_state_pre_settlement",
                message="Pre-settlement audit requires an authorized state.",
            )
        ]
        return IntegrityCheckResult(issues=issues)
    return result


def audit_post_settlement(payload: TransactionPayload) -> IntegrityCheckResult:
    """Run EFCTIA post-settlement integrity audit."""

    validator = TransactionIntegrityValidator()
    result = validator.validate(payload)
    if payload.state not in {TransactionState.SETTLED, TransactionState.FINALIZED}:
        issues = result.issues + [
            IntegrityIssue(
                code="invalid_state_post_settlement",
                message="Post-settlement audit requires settled or finalized state.",
            )
        ]
        return IntegrityCheckResult(issues=issues)
    if payload.settled_at is None:
        issues = result.issues + [
            IntegrityIssue(
                code="missing_settlement_timestamp",
                message="Post-settlement audit requires settlement timestamp.",
            )
        ]
        return IntegrityCheckResult(issues=issues)
    return result


def validate_batch(
    payloads: Iterable[TransactionPayload], *, allow_deferred: bool = False
) -> dict[str, object]:
    """Validate a batch of transactions with optional deferred audits."""

    validator = TransactionIntegrityValidator()
    results: list[dict[str, object]] = []
    deferred: list[str] = []
    for payload in payloads:
        result = validator.validate(payload)
        if not result.is_valid and allow_deferred:
            deferred.append(payload.transaction_id)
        results.append({
            "transaction_id": payload.transaction_id,
            "valid": result.is_valid,
            "issues": [issue.__dict__ for issue in result.issues],
        })
    return {"results": results, "deferred": deferred}


def dbis_settlement_gate(payload: TransactionPayload) -> IntegrityCheckResult:
    """Gate DBIS settlement finality on EFCTIA validation."""

    result = audit_post_settlement(payload)
    if not result.is_valid:
        return result
    return result
