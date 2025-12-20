"""Simulation utilities for DBIS systemic risk testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from uuid import uuid4

from .engine import ComplianceProfile, DbisEngine, TransactionIntent


@dataclass(frozen=True)
class StressScenario:
    scenario_id: str
    description: str
    intents: tuple[TransactionIntent, ...]
    expected_failure_rate: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "expected_failure_rate": self.expected_failure_rate,
            "intents": [intent.as_dict() for intent in self.intents],
        }


class DbisStressTester:
    """Run simulations without emitting settlement receipts."""

    def __init__(self, *, dbis: DbisEngine) -> None:
        self.dbis = dbis

    def build_scenario(
        self,
        intents: Iterable[TransactionIntent],
        *,
        description: str,
        expected_failure_rate: float,
    ) -> StressScenario:
        return StressScenario(
            scenario_id=str(uuid4()),
            description=description,
            intents=tuple(intents),
            expected_failure_rate=expected_failure_rate,
        )

    def evaluate(
        self,
        scenario: StressScenario,
        compliance: ComplianceProfile,
    ) -> dict[str, Any]:
        failures = 0
        diagnostics: list[dict[str, Any]] = []
        for intent in scenario.intents:
            issues = self.dbis.validate_intent(intent, compliance)
            if issues:
                failures += 1
            diagnostics.append(
                {
                    "intent_id": intent.intent_id,
                    "issues": issues,
                }
            )
        failure_rate = failures / max(len(scenario.intents), 1)
        return {
            "scenario": scenario.as_dict(),
            "failure_rate": failure_rate,
            "within_expected_bounds": failure_rate <= scenario.expected_failure_rate,
            "diagnostics": diagnostics,
        }


__all__ = ["DbisStressTester", "StressScenario"]
