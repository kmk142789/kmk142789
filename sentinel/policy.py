from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .utils import Finding, isoformat


@dataclass(slots=True)
class PolicyDecision:
    level: str
    message: str
    rationale: dict[str, Any]


class PolicyEngine:
    """Very small policy evaluation engine.

    Policies can mark drift as a *quarantine* event which will later instruct the
    remedy planner to isolate the subject instead of trying a direct fix.
    """

    def __init__(self, quarantine_threshold: int = 1) -> None:
        self.quarantine_threshold = quarantine_threshold

    def evaluate(self, findings: Iterable[Finding]) -> list[PolicyDecision]:
        quarantined: dict[str, list[Finding]] = {}
        decisions: list[PolicyDecision] = []

        for finding in findings:
            if finding.status != "error":
                continue
            quarantined.setdefault(finding.subject, []).append(finding)

        for subject, subject_findings in quarantined.items():
            if len(subject_findings) >= self.quarantine_threshold:
                decisions.append(
                    PolicyDecision(
                        level="quarantine",
                        message=f"Quarantine required for {subject}",
                        rationale={
                            "subject": subject,
                            "findings": [finding.message for finding in subject_findings],
                            "evaluated_at": isoformat(),
                        },
                    )
                )

        return decisions


__all__ = ["PolicyDecision", "PolicyEngine"]

