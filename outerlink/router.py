from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .events import EventBus
from .utils import OfflineState


@dataclass
class RoutingDecision:
    task: str
    target: str
    reason: str
    fallback_used: bool = False


class TaskRouter:
    """Routes tasks between local submodules with deterministic fallbacks."""

    def __init__(self, event_bus: EventBus, offline_state: OfflineState) -> None:
        self.event_bus = event_bus
        self.offline_state = offline_state
        self.registry: Dict[str, str] = {}

    def register_module(self, task: str, module_name: str) -> None:
        self.registry[task] = module_name

    def route(self, task: str, payload: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        target = self.registry.get(task, "default")
        reason = "Registered mapping" if task in self.registry else "Default fallback"
        fallback = False
        if not self.offline_state.online and target == "default":
            target = "offline_fallback"
            fallback = True
            reason = "Offline mode fallback"
        decision = RoutingDecision(task=task, target=target, reason=reason, fallback_used=fallback)
        self.event_bus.emit("task_routed", {"task": task, "target": target, "fallback": fallback})
        return decision

    def resolve_conflict(self, tasks: List[str]) -> RoutingDecision:
        ordered = sorted(tasks)
        winner = ordered[0]
        decision = RoutingDecision(
            task=winner,
            target=self.registry.get(winner, "default"),
            reason="Lexicographic tie-break",
            fallback_used=not self.offline_state.online,
        )
        self.event_bus.emit("conflict_resolved", {"winner": winner, "tasks": ordered})
        return decision


__all__ = ["TaskRouter", "RoutingDecision"]
