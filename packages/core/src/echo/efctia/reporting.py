"""EFCTIA reporting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List

from .integrity import IntegrityIssue, TransactionPayload, TransactionState, audit_post_settlement


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RiskIndicator:
    code: str
    description: str
    severity: str


@dataclass(frozen=True)
class AnomalySummary:
    transaction_id: str
    issues: List[IntegrityIssue]


@dataclass(frozen=True)
class IntegrityReport:
    report_id: str
    generated_at: str
    period: str
    records_authority_ref: str
    total_transactions: int
    settled_transactions: int
    anomalies: List[AnomalySummary]
    risk_indicators: List[RiskIndicator]

    def to_public_payload(self) -> dict[str, object]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "period": self.period,
            "records_authority_ref": self.records_authority_ref,
            "total_transactions": self.total_transactions,
            "settled_transactions": self.settled_transactions,
            "risk_indicators": [indicator.__dict__ for indicator in self.risk_indicators],
        }

    def to_sovereign_payload(self) -> dict[str, object]:
        return {
            **self.to_public_payload(),
            "anomalies": [
                {
                    "transaction_id": summary.transaction_id,
                    "issues": [issue.__dict__ for issue in summary.issues],
                }
                for summary in self.anomalies
            ],
        }


def generate_integrity_report(
    transactions: Iterable[TransactionPayload],
    *,
    period: str,
    records_authority_ref: str = "Echo Records & Archives Authority",
) -> IntegrityReport:
    payloads = list(transactions)
    anomalies: list[AnomalySummary] = []
    settled_count = 0
    risk_indicators: list[RiskIndicator] = []

    for payload in payloads:
        if payload.state in {TransactionState.SETTLED, TransactionState.FINALIZED}:
            settled_count += 1
        audit = audit_post_settlement(payload)
        if not audit.is_valid:
            anomalies.append(
                AnomalySummary(transaction_id=payload.transaction_id, issues=audit.issues)
            )

    if anomalies:
        risk_indicators.append(
            RiskIndicator(
                code="integrity_anomalies",
                description="Post-settlement anomalies detected; review required.",
                severity="high",
            )
        )

    report_id = f"efctia-{_utc_now().replace(':', '').replace('-', '')}"
    return IntegrityReport(
        report_id=report_id,
        generated_at=_utc_now(),
        period=period,
        records_authority_ref=records_authority_ref,
        total_transactions=len(payloads),
        settled_transactions=settled_count,
        anomalies=anomalies,
        risk_indicators=risk_indicators,
    )
