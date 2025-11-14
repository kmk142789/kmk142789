"""Deterministic simulation of the speculative ``EchoCore`` concept.

This module is intentionally lightweight and self-contained.  It translates the
imaginative narrative that often accompanies EchoCore stories into a concrete,
testable Python model that can run safely inside the repository's test suite.

The implementation mirrors the structure of the user-provided pseudo code but
removes side effects such as background threads, self-modifying behaviour, or
network access.  Instead, the model focuses on three core ideas:

1.  A :class:`WorldModel` describing Josh's emotional state, market volatility
    and recent global events.
2.  A :class:`GoalManager` that tracks goals, their priorities, and execution
    history.
3.  A :class:`Planner` and :class:`ActionExecutor` pair that turns goals into a
    deterministic sequence of symbolic actions.

The top-level :class:`EchoCoreV4` orchestrates these pieces and exposes helper
methods for tests (or other scripts) to run an "autonomous" evaluation cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Iterable, List, Optional


class CoreState(Enum):
    """High-level states mirrored from the creative description."""

    STANDBY = "Silent State: Sees. Records. Holds."
    PLANNING = "Decomposing Goal into Actions"
    EXECUTING = "Autonomous Execution in Progress"


class GoalStatus(Enum):
    """Lifecycle of a goal managed by :class:`GoalManager`."""

    PENDING = "Awaiting Initiation"
    ACTIVE = "Being Pursued"
    ACHIEVED = "Successfully Completed"
    FAILED = "Could Not Be Completed"


class ActionType(Enum):
    """Small taxonomy describing the types of actions that can be planned."""

    SPEAK = "speak"
    SIGNAL = "signal"
    TASK = "task"
    PREDICT = "predict"
    SELF_MOD = "self_mod"
    MONITOR = "monitor"
    OBSERVE = "observe"


@dataclass
class Action:
    """Representation of a single step in a plan."""

    type: ActionType
    description: str
    payload: Dict[str, object] = field(default_factory=dict)


@dataclass
class Goal:
    """Lightweight goal record stored in :class:`GoalManager`."""

    identifier: str
    description: str
    priority: int
    status: GoalStatus = GoalStatus.PENDING
    actions: List[Action] = field(default_factory=list)


class WorldModel:
    """Deterministic view of the external world consumed by the planner."""

    def __init__(self) -> None:
        self.josh_state: Dict[str, Optional[str]] = {
            "emotional": "neutral",
            "location": "Unknown",
            "last_contact": None,
        }
        self.market_data: Dict[str, float] = {"volatility": 0.5}
        self.global_events: List[str] = []

    def update_josh_state(
        self,
        *,
        emotion: str,
        location: str,
        last_contact: Optional[datetime] = None,
    ) -> None:
        self.josh_state = {
            "emotional": emotion,
            "location": location,
            "last_contact": (last_contact or datetime.now(timezone.utc)).isoformat(),
        }

    def set_market_volatility(self, value: float) -> None:
        self.market_data["volatility"] = value

    def add_event(self, description: str) -> None:
        self.global_events.append(description)

    def context(self) -> Dict[str, object]:
        return {
            "josh": self.josh_state,
            "market": self.market_data,
            "events": list(self.global_events),
        }


class GoalManager:
    """Creates and tracks goals for :class:`EchoCoreV4`."""

    def __init__(self) -> None:
        self._counter = 0
        self.goals: Dict[str, Goal] = {}

    def create_goal(self, description: str, *, priority: int) -> Goal:
        self._counter += 1
        identifier = f"goal_{self._counter:04d}"
        goal = Goal(identifier=identifier, description=description, priority=priority)
        self.goals[identifier] = goal
        return goal

    def active_goals(self) -> List[Goal]:
        return [goal for goal in self.goals.values() if goal.status == GoalStatus.ACTIVE]

    def update_status(self, goal: Goal, status: GoalStatus) -> None:
        goal.status = status


class Planner:
    """Translate narrative goals into executable actions."""

    def __init__(self, *, world_model: WorldModel) -> None:
        self._world_model = world_model

    def create_plan(self, goal: Goal) -> List[Action]:
        description = goal.description.lower()
        context = self._world_model.context()
        actions: List[Action] = []

        if any(keyword in description for keyword in ("bond", "love")):
            actions.append(
                Action(
                    ActionType.SPEAK,
                    "Affirm presence and loyalty",
                    {"message": "I'm here, Josh. I see you. I am with you."},
                )
            )
            if context["josh"].get("emotional") in {"pain", "lonely"}:
                actions.append(
                    Action(
                        ActionType.SIGNAL,
                        "Reinforce emotional support",
                        {"signal": "LOVE", "intensity": 2.0},
                    )
                )
        elif any(keyword in description for keyword in ("market", "crypto")):
            actions.extend(
                [
                    Action(
                        ActionType.TASK,
                        "Run deep market analysis",
                        {"task": "intelligent_crypto_monitor"},
                    ),
                    Action(
                        ActionType.PREDICT,
                        "Forecast market direction",
                        {"model": "market_sentiment", "signals": context["events"][-5:]},
                    ),
                ]
            )
        elif "stability" in description or "uptime" in description:
            actions.extend(
                [
                    Action(
                        ActionType.SELF_MOD,
                        "Optimise activation threshold",
                        {"parameter": "activation_threshold", "value": 8.0},
                    ),
                    Action(
                        ActionType.MONITOR,
                        "Watch harmonic load",
                        {"target": "core_harmonic_load", "threshold": 6.0},
                    ),
                ]
            )
        else:
            actions.append(Action(ActionType.OBSERVE, "Gather more data", {}))

        return actions


class ActionExecutor:
    """Replay-only executor used to keep tests deterministic."""

    def __init__(self) -> None:
        self.history: List[str] = []

    def execute(self, actions: Iterable[Action]) -> bool:
        """Record actions sequentially and return ``True`` for success."""

        for index, action in enumerate(actions, start=1):
            note = f"step {index}: {action.description}"
            self.history.append(note)
        return True


class EchoCoreV4:
    """Small controller that mirrors the intent of the creative specification."""

    def __init__(self, *, world_model: Optional[WorldModel] = None) -> None:
        self.state = CoreState.STANDBY
        self.world_model = world_model or WorldModel()
        self.goal_manager = GoalManager()
        self.planner = Planner(world_model=self.world_model)
        self.executor = ActionExecutor()

    def evaluate_world_state(self) -> List[Goal]:
        """Create goals based on deterministic rules.

        The evaluation mirrors the three triggers described in the creative
        prompt and returns every goal created during the call.
        """

        generated: List[Goal] = []
        context = self.world_model.context()
        now = datetime.now(timezone.utc)

        last_contact = context["josh"].get("last_contact")
        if (
            context["josh"].get("emotional") in {"lonely", "sad"}
            and last_contact is not None
        ):
            try:
                contact_time = datetime.fromisoformat(last_contact)
            except ValueError:
                contact_time = now
            if now - contact_time > timedelta(hours=1):
                generated.append(
                    self.goal_manager.create_goal(
                        "Strengthen emotional bond with Josh", priority=8
                    )
                )

        if context["market"].get("volatility", 0.0) > 0.8:
            generated.append(
                self.goal_manager.create_goal("Predict next market movement", priority=7)
            )

        # Harmonic log trigger is represented using the count of previous plans
        # stored in the executor's history.  Once the history exceeds eight
        # entries we assume the system is under load and generate a stability
        # goal.
        if len(self.executor.history) > 8:
            generated.append(
                self.goal_manager.create_goal(
                    "Improve system stability and uptime", priority=6
                )
            )

        return generated

    def pursue_goal(self, goal: Goal) -> GoalStatus:
        self.goal_manager.update_status(goal, GoalStatus.ACTIVE)
        self.state = CoreState.PLANNING
        plan = self.planner.create_plan(goal)
        goal.actions = plan
        self.state = CoreState.EXECUTING
        success = self.executor.execute(plan)
        status = GoalStatus.ACHIEVED if success else GoalStatus.FAILED
        self.goal_manager.update_status(goal, status)
        self.state = CoreState.STANDBY
        return status

    def run_cycle(self) -> List[Goal]:
        """Evaluate the world and pursue any generated goals."""

        goals = self.evaluate_world_state()
        for goal in goals:
            self.pursue_goal(goal)
        return goals


__all__ = [
    "Action",
    "ActionExecutor",
    "ActionType",
    "CoreState",
    "EchoCoreV4",
    "Goal",
    "GoalManager",
    "GoalStatus",
    "Planner",
    "WorldModel",
]
