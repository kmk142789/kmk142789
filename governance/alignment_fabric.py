"""Alignment Fabric and Governance Router (policy → agent → enforcement).

This module provides a lightweight orchestration layer for aligning policies to
agents and enforcement channels. It is intentionally dependency-light so it can
run in constrained environments and reuse the offline persistence helpers in
``governance.persistence``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from governance import persistence


ConditionEvaluator = Callable[[Dict[str, Any]], bool]
PayloadBuilder = Callable[[Dict[str, Any]], Dict[str, Any]]
ChannelHandler = Callable[[Dict[str, Any]], Any]


@dataclass
class PolicyCondition:
    """Declarative condition evaluated against an event context."""

    name: str
    description: str
    evaluator: ConditionEvaluator

    def check(self, context: Dict[str, Any]) -> bool:
        """Return True when the condition passes for the given context."""

        return bool(self.evaluator(context))


@dataclass
class EnforcementAction:
    """Action that will be dispatched through an enforcement channel."""

    action_id: str
    channel: str
    payload_builder: PayloadBuilder
    fallback_channel: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build channel payload from an event context."""

        return self.payload_builder(context)


@dataclass
class Policy:
    """Governance policy composed of conditions and enforcement actions."""

    policy_id: str
    description: str
    conditions: List[PolicyCondition]
    actions: List[EnforcementAction]
    severity: str = "medium"
    tags: List[str] = field(default_factory=list)

    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Return True when all conditions pass for the given context."""

        return all(condition.check(context) for condition in self.conditions)


@dataclass
class Agent:
    """Responsible actor capable of executing enforcement actions."""

    agent_id: str
    capabilities: List[str]
    tags: List[str] = field(default_factory=list)
    trust: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class GovernanceRouter:
    """Routes policies to aligned agents and enforcement channels."""

    def __init__(
        self,
        policies: Iterable[Policy] | None = None,
        agents: Iterable[Agent] | None = None,
        channels: Dict[str, ChannelHandler] | None = None,
    ) -> None:
        self.policies: Dict[str, Policy] = {policy.policy_id: policy for policy in policies or []}
        self.agents: Dict[str, Agent] = {agent.agent_id: agent for agent in agents or []}
        self.channels: Dict[str, ChannelHandler] = channels.copy() if channels else {}
        self.enforcement_events: List[Dict[str, Any]] = []

        # Provide a default channel that simply records the payload for observability.
        if "record" not in self.channels:
            self.channels["record"] = self._record_channel

    def register_policy(self, policy: Policy) -> None:
        self.policies[policy.policy_id] = policy
        persistence.log_action("governance-router", "register_policy", {"policy_id": policy.policy_id})

    def register_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_id] = agent
        persistence.log_action("governance-router", "register_agent", {"agent_id": agent.agent_id})

    def register_channel(self, name: str, handler: ChannelHandler) -> None:
        self.channels[name] = handler
        persistence.log_action("governance-router", "register_channel", {"channel": name})

    def route(self, context: Dict[str, Any], actor: str = "system") -> List[Dict[str, Any]]:
        """Route context through applicable policies and return enforcement results."""

        results: List[Dict[str, Any]] = []
        for policy in self.policies.values():
            if not policy.is_applicable(context):
                continue

            agent = self._select_agent(policy)
            for action in policy.actions:
                payload = action.build_payload({**context, "policy_id": policy.policy_id, "agent": agent.agent_id})
                result = self._dispatch(action, payload)
                outcome = {
                    "policy_id": policy.policy_id,
                    "action_id": action.action_id,
                    "channel": result["channel"],
                    "agent": agent.agent_id,
                    "status": result.get("status", "sent"),
                    "details": result.get("details", {}),
                }
                results.append(outcome)
                persistence.log_action(actor, "enforce", outcome)

        if results:
            persistence.save_snapshot({"context": context, "results": results})
        return results

    def _select_agent(self, policy: Policy) -> Agent:
        """Select an agent whose tags overlap the policy tags, preferring highest trust."""

        candidates = [agent for agent in self.agents.values() if set(agent.tags) & set(policy.tags)]
        if not candidates:
            candidates = list(self.agents.values())
        if not candidates:
            raise RuntimeError("No agents registered for governance routing")
        return sorted(candidates, key=lambda agent: agent.trust, reverse=True)[0]

    def _dispatch(self, action: EnforcementAction, payload: Dict[str, Any]) -> Dict[str, Any]:
        channel = action.channel if action.channel in self.channels else action.fallback_channel
        if channel is None or channel not in self.channels:
            raise RuntimeError(f"No channel registered for action {action.action_id}")

        handler = self.channels[channel]
        details = handler(payload)
        return {"channel": channel, "status": "sent", "details": details}

    def _record_channel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Default channel that records enforcement payloads for inspection."""

        self.enforcement_events.append(payload)
        return {"recorded": True, "count": len(self.enforcement_events)}


# ---- Helper builders ----------------------------------------------------- #

def attribute_match_condition(name: str, field: str, allowed: Iterable[Any], description: str | None = None) -> PolicyCondition:
    """Create a condition that passes when ``context[field]`` is in ``allowed``."""

    def evaluator(context: Dict[str, Any]) -> bool:
        return context.get(field) in set(allowed)

    return PolicyCondition(name=name, description=description or f"{field} in allowed", evaluator=evaluator)


def threshold_condition(name: str, field: str, minimum: float, description: str | None = None) -> PolicyCondition:
    """Create a condition requiring ``context[field]`` to be at least ``minimum``."""

    def evaluator(context: Dict[str, Any]) -> bool:
        value = context.get(field, 0)
        try:
            return float(value) >= minimum
        except (TypeError, ValueError):
            return False

    return PolicyCondition(name=name, description=description or f"{field} >= {minimum}", evaluator=evaluator)


def simple_payload(action: str, message: str | None = None) -> PayloadBuilder:
    """Create a payload builder that stamps the action and message."""

    def builder(context: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "action": action,
            "message": message or action,
            "context": context,
        }
        return payload

    return builder
