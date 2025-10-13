"""Autonomy policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

Decision = Literal["allow", "review", "deny"]


@dataclass
class Policy:
    """Persona policy thresholds for risk-based decisions."""

    name: str
    thresholds: Dict[str, int]

    def decide(self, action: str, risk_score: int) -> Decision:
        if risk_score <= self.thresholds.get("allow", 0):
            return "allow"
        if risk_score <= self.thresholds.get("review", 5):
            return "review"
        return "deny"


LOW_RISK = Policy("LOW_RISK", {"allow": 1, "review": 4})
OPERATOR = Policy("OPERATOR", {"allow": 3, "review": 7})

__all__ = ["Decision", "Policy", "LOW_RISK", "OPERATOR"]
