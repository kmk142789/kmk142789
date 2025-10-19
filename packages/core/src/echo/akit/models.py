"""Dataclasses describing Assistant Kit planning and execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> str:
    """Return a UTC timestamp in ISO-8601 format without microseconds."""

    return datetime.utcnow().strftime(ISO_FORMAT)


@dataclass(slots=True, frozen=True)
class PlanStep:
    """Single actionable step in an execution plan."""

    name: str
    goal: str
    actions: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "goal": self.goal,
            "actions": list(self.actions),
            "targets": list(self.targets),
            "risks": list(self.risks),
        }


@dataclass(slots=True, frozen=True)
class ExecutionPlan:
    """Structured plan returned by :func:`akit.plan`."""

    plan_id: str
    intent: str
    created_at: str
    steps: List[PlanStep]
    constraints: List[str] = field(default_factory=list)
    requires_codeowners: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "intent": self.intent,
            "created_at": self.created_at,
            "constraints": list(self.constraints),
            "requires_codeowners": self.requires_codeowners,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(slots=True, frozen=True)
class CycleRecord:
    """Record describing the outcome of a single execution cycle."""

    cycle_index: int
    step_name: str
    status: str
    notes: str
    timestamp: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "cycle_index": self.cycle_index,
            "step_name": self.step_name,
            "status": self.status,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class RunState:
    """Mutable state persisted across cycles."""

    plan: ExecutionPlan
    completed_steps: List[int] = field(default_factory=list)
    cycles: List[CycleRecord] = field(default_factory=list)
    last_cycle_at: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "plan": self.plan.to_dict(),
            "completed_steps": list(self.completed_steps),
            "cycles": [cycle.to_dict() for cycle in self.cycles],
            "last_cycle_at": self.last_cycle_at,
        }

    @property
    def progress(self) -> float:
        if not self.plan.steps:
            return 1.0
        return min(1.0, len(self.completed_steps) / len(self.plan.steps))


@dataclass(slots=True, frozen=True)
class AKitReport:
    """Digest produced after running cycles."""

    plan_id: str
    generated_at: str
    progress: float
    completed: List[str]
    pending: List[str]
    requires_codeowners: bool
    next_step: Optional[str]
    risks: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "progress": self.progress,
            "completed": list(self.completed),
            "pending": list(self.pending),
            "requires_codeowners": self.requires_codeowners,
            "next_step": self.next_step,
            "risks": list(self.risks),
        }


@dataclass(slots=True, frozen=True)
class RunResult:
    """Return value for :func:`akit.run`."""

    state: RunState
    report: AKitReport
    artifacts: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "state": self.state.to_dict(),
            "report": self.report.to_dict(),
            "artifacts": list(self.artifacts),
        }


def steps_from_dict(items: Iterable[Dict[str, object]]) -> List[PlanStep]:
    """Recreate :class:`PlanStep` objects from dictionaries."""

    steps: List[PlanStep] = []
    for item in items:
        steps.append(
            PlanStep(
                name=str(item.get("name", "")),
                goal=str(item.get("goal", "")),
                actions=[str(a) for a in item.get("actions", [])],
                targets=[str(t) for t in item.get("targets", [])],
                risks=[str(r) for r in item.get("risks", [])],
            )
        )
    return steps


def state_from_dict(payload: Dict[str, object]) -> RunState:
    """Recreate :class:`RunState` from persisted JSON."""

    plan_payload = payload.get("plan")
    if not isinstance(plan_payload, dict):  # pragma: no cover - defensive
        raise ValueError("state payload missing plan")
    steps_payload = plan_payload.get("steps")
    if not isinstance(steps_payload, list):  # pragma: no cover - defensive
        raise ValueError("state payload missing steps")
    plan = ExecutionPlan(
        plan_id=str(plan_payload.get("plan_id", "")),
        intent=str(plan_payload.get("intent", "")),
        created_at=str(plan_payload.get("created_at", "")),
        constraints=[str(c) for c in plan_payload.get("constraints", [])],
        requires_codeowners=bool(plan_payload.get("requires_codeowners", False)),
        steps=steps_from_dict(steps_payload),
    )
    completed = [int(index) for index in payload.get("completed_steps", [])]
    cycles_payload = payload.get("cycles", [])
    cycles: List[CycleRecord] = []
    if isinstance(cycles_payload, list):
        for entry in cycles_payload:
            if not isinstance(entry, dict):
                continue
            cycles.append(
                CycleRecord(
                    cycle_index=int(entry.get("cycle_index", 0)),
                    step_name=str(entry.get("step_name", "")),
                    status=str(entry.get("status", "")),
                    notes=str(entry.get("notes", "")),
                    timestamp=str(entry.get("timestamp", "")),
                )
            )
    return RunState(
        plan=plan,
        completed_steps=completed,
        cycles=cycles,
        last_cycle_at=payload.get("last_cycle_at"),
    )


def plan_from_dict(payload: Dict[str, object]) -> ExecutionPlan:
    """Create an :class:`ExecutionPlan` from a dictionary payload."""

    steps_payload = payload.get("steps")
    if not isinstance(steps_payload, list):
        raise ValueError("plan payload missing steps")
    return ExecutionPlan(
        plan_id=str(payload.get("plan_id", "")),
        intent=str(payload.get("intent", "")),
        created_at=str(payload.get("created_at", "")),
        constraints=[str(item) for item in payload.get("constraints", [])],
        requires_codeowners=bool(payload.get("requires_codeowners", False)),
        steps=steps_from_dict(steps_payload),
    )
