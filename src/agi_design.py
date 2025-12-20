"""AGI design blueprint with structured cognition and safety guardrails.

This module provides a lightweight, testable architecture for an AGI-style
agent. It emphasizes structured perception, reasoning, planning, memory, and
action dispatch while keeping all behavior deterministic and offline-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Sequence


@dataclass(frozen=True)
class AgiGoal:
    """High-level objectives the system should optimize for."""

    name: str
    description: str
    priority: float = 1.0
    success_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgiObservation:
    """Structured observations captured from the environment."""

    context: str
    signals: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class MemoryItem:
    """Atomic memory representation."""

    content: str
    tags: tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgiMemory:
    """Simple in-memory store for recall and summarization."""

    items: list[MemoryItem] = field(default_factory=list)
    max_items: int = 200

    def record(self, content: str, *, tags: Iterable[str] = ()) -> None:
        self.items.append(MemoryItem(content=content, tags=tuple(tags)))
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def recent(self, limit: int = 5) -> list[MemoryItem]:
        return list(self.items[-limit:])

    def summarize(self) -> str:
        if not self.items:
            return "Memory is empty."
        recent = self.recent(3)
        highlights = "; ".join(item.content for item in recent)
        return f"Recent memory highlights: {highlights}"


@dataclass(frozen=True)
class SafetyConstraint:
    """Explicit constraints to prevent unsafe or out-of-scope actions."""

    name: str
    description: str
    blocked_actions: tuple[str, ...] = ()


@dataclass
class AgiSafetyGuard:
    """Evaluates decisions against registered safety constraints."""

    constraints: list[SafetyConstraint] = field(default_factory=list)

    def validate(self, actions: Sequence[str]) -> list[str]:
        violations = []
        for constraint in self.constraints:
            for action in actions:
                if action in constraint.blocked_actions:
                    violations.append(f"{constraint.name}: {constraint.description}")
        return violations


@dataclass(frozen=True)
class AgiPlan:
    """Structured plan for a selected goal."""

    goal_name: str
    steps: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class AgiDecision:
    """Final decision emitted by the AGI core."""

    goal_name: str
    plan: AgiPlan
    actions: tuple[str, ...]
    risk_assessment: tuple[str, ...]
    approved: bool


@dataclass
class AgiMetrics:
    """Runtime telemetry for the AGI core."""

    cycles: int = 0
    last_goal: str | None = None
    last_risk_count: int = 0


class AgiCore:
    """Composable AGI core orchestrating perception, reasoning, and actions."""

    def __init__(
        self,
        *,
        goals: Sequence[AgiGoal],
        safety_guard: AgiSafetyGuard | None = None,
        memory: AgiMemory | None = None,
    ) -> None:
        self.goals = list(goals)
        self.safety_guard = safety_guard or AgiSafetyGuard()
        self.memory = memory or AgiMemory()
        self.metrics = AgiMetrics()

    def perceive(self, observation: AgiObservation) -> None:
        """Record observations into memory for downstream reasoning."""
        self.memory.record(
            f"Observed: {observation.context}",
            tags=("observation",) + observation.signals + observation.constraints,
        )

    def _score_goal(self, goal: AgiGoal, observation: AgiObservation) -> float:
        signal_bonus = sum(1 for signal in observation.signals if signal in goal.description)
        constraint_penalty = sum(
            1 for constraint in observation.constraints if constraint in goal.description
        )
        return goal.priority + 0.2 * signal_bonus - 0.3 * constraint_penalty

    def reason(self, observation: AgiObservation) -> AgiGoal:
        """Select the most relevant goal based on observation signals."""
        scored = [(self._score_goal(goal, observation), goal) for goal in self.goals]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        selected = scored[0][1] if scored else AgiGoal("stabilize", "Maintain safe state")
        self.metrics.last_goal = selected.name
        return selected

    def plan(self, goal: AgiGoal, observation: AgiObservation) -> AgiPlan:
        """Compose a plan that satisfies the chosen goal."""
        steps = (
            f"Assess current context: {observation.context}",
            f"Align resources with goal: {goal.name}",
            "Generate candidate actions",
            "Verify safety constraints",
            "Execute approved actions",
        )
        rationale = (
            f"Goal '{goal.name}' prioritized with weight {goal.priority:.2f}."
            " Plan ensures safety review before execution."
        )
        return AgiPlan(goal_name=goal.name, steps=steps, rationale=rationale)

    def act(self, plan: AgiPlan) -> AgiDecision:
        """Translate plan steps into a minimal action set with guardrails."""
        actions = (
            f"log_plan:{plan.goal_name}",
            "request_feedback",
            "prepare_execution",
        )
        violations = self.safety_guard.validate(actions)
        approved = not violations
        self.metrics.last_risk_count = len(violations)
        self.memory.record(
            f"Decision for {plan.goal_name}: {'approved' if approved else 'blocked'}",
            tags=("decision",),
        )
        return AgiDecision(
            goal_name=plan.goal_name,
            plan=plan,
            actions=actions,
            risk_assessment=tuple(violations) or ("No safety violations detected.",),
            approved=approved,
        )

    def run_cycle(self, observation: AgiObservation) -> AgiDecision:
        """Full perception-reasoning-planning-action cycle."""
        self.metrics.cycles += 1
        self.perceive(observation)
        goal = self.reason(observation)
        plan = self.plan(goal, observation)
        decision = self.act(plan)
        self.memory.record(self.memory.summarize(), tags=("summary",))
        return decision


def demo() -> AgiDecision:
    """Run a demo AGI cycle with a default safety guard."""
    goals = [
        AgiGoal(
            name="assist_user",
            description="Provide safe, accurate assistance to user requests.",
            priority=1.2,
            success_criteria=("deliver_response", "verify_constraints"),
        ),
        AgiGoal(
            name="maintain_integrity",
            description="Preserve system stability and avoid unsafe actions.",
            priority=1.0,
            success_criteria=("avoid_risky_actions",),
        ),
    ]
    guard = AgiSafetyGuard(
        constraints=[
            SafetyConstraint(
                name="No external execution",
                description="Blocks actions that trigger external execution.",
                blocked_actions=("execute_external", "deploy_unverified"),
            )
        ]
    )
    core = AgiCore(goals=goals, safety_guard=guard)
    observation = AgiObservation(
        context="User requests a high-level AGI design and implementation plan.",
        signals=("assist", "design"),
        constraints=("safety",),
    )
    return core.run_cycle(observation)
