"""Policy enforcement for Dominion plans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from .plans import DominionPlan


class PolicyViolation(RuntimeError):
    """Raised when a plan violates configured policy constraints."""


@dataclass
class AllowlistPolicy:
    allowed_actions: set[str] = field(default_factory=set)

    def enforce(self, plan: DominionPlan) -> None:
        disallowed = {intent.action_type for intent in plan.intents if intent.action_type not in self.allowed_actions}
        if disallowed:
            raise PolicyViolation(f"Disallowed action types: {', '.join(sorted(disallowed))}")


@dataclass
class RedactionPolicy:
    keys: set[str] = field(default_factory=set)
    replacement: str = "***"

    def redact_mapping(self, payload: Mapping[str, object]) -> dict[str, object]:
        return {key: (self.replacement if key in self.keys else value) for key, value in payload.items()}


@dataclass
class IdempotencyPolicy:
    state_path: Path

    def __post_init__(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self.state_path.write_text(json.dumps({"applied": []}, indent=2), encoding="utf-8")

    def _load(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _store(self, data: dict) -> None:
        self.state_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def enforce(self, plan: DominionPlan) -> None:
        data = self._load()
        if plan.plan_id in data.get("applied", []):
            raise PolicyViolation(f"Plan {plan.plan_id} has already been applied")

    def mark_applied(self, plan: DominionPlan) -> None:
        data = self._load()
        applied = set(data.get("applied", []))
        applied.add(plan.plan_id)
        data["applied"] = sorted(applied)
        self._store(data)

    def rollback(self, plan: DominionPlan) -> None:
        data = self._load()
        applied = set(data.get("applied", []))
        if plan.plan_id in applied:
            applied.remove(plan.plan_id)
            data["applied"] = sorted(applied)
            self._store(data)


@dataclass
class PolicyEngine:
    allowlist: AllowlistPolicy
    redaction: RedactionPolicy
    idempotency: IdempotencyPolicy

    def validate(self, plan: DominionPlan) -> None:
        self.allowlist.enforce(plan)
        self.idempotency.enforce(plan)

    def redact(self, payload: Mapping[str, object]) -> dict[str, object]:
        return self.redaction.redact_mapping(payload)

    def mark_applied(self, plan: DominionPlan) -> None:
        self.idempotency.mark_applied(plan)

    def rollback(self, plan: DominionPlan) -> None:
        self.idempotency.rollback(plan)

