"""Alignment Fabric and Governance Router (policy → agent → enforcement).

This module provides a lightweight orchestration layer for aligning policies to
agents and enforcement channels. It is intentionally dependency-light so it can
run in constrained environments and reuse the offline persistence helpers in
``governance.persistence``.
"""

from __future__ import annotations

import ast
import operator
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from governance import persistence


ConditionEvaluator = Callable[[Dict[str, Any]], bool]
PayloadBuilder = Callable[[Dict[str, Any]], Dict[str, Any]]
ChannelHandler = Callable[[Dict[str, Any]], Any]
DynamicCallback = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any] | None]


class ConditionLanguage:
    """Minimal, safe condition language compiler for offline policy checks."""

    OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }

    def __init__(self, expression: str) -> None:
        self.expression = expression
        self._tree = ast.parse(expression, mode="eval")
        self._validate(self._tree.body)

    def evaluator(self, context: Dict[str, Any]) -> bool:
        return bool(self._eval(self._tree.body, context))

    def _validate(self, node: ast.AST) -> None:
        if isinstance(node, (ast.And, ast.Or, ast.cmpop, ast.Load)):
            return
        allowed_nodes = (
            ast.BoolOp,
            ast.Compare,
            ast.Name,
            ast.Constant,
            ast.List,
            ast.Tuple,
            ast.Attribute,
        )
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")
        for child in ast.iter_child_nodes(node):
            self._validate(child)

    def _eval(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        if isinstance(node, ast.BoolOp):
            values = [self._eval(value, context) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError("Unsupported boolean operator")
        if isinstance(node, ast.Compare):
            left = self._eval(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval(comparator, context)
                operator_fn = self.OPERATORS.get(type(op))
                if operator_fn is None:
                    raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
                if not operator_fn(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Name):
            return context.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self._eval(node.value, context)
            return self._resolve_attribute(base, node.attr)
        if isinstance(node, (ast.Constant, ast.List, ast.Tuple)):
            return ast.literal_eval(ast.unparse(node))
        raise ValueError(f"Unsupported expression component: {type(node).__name__}")

    def _resolve_attribute(self, value: Any, attribute: str) -> Any:
        if attribute.startswith("__"):
            raise ValueError("Unsafe attribute access attempted")
        if isinstance(value, dict):
            return value.get(attribute)
        return getattr(value, attribute, None)


@dataclass
class PolicyCondition:
    """Declarative condition evaluated against an event context."""

    name: str
    description: str
    evaluator: ConditionEvaluator

    def check(self, context: Dict[str, Any]) -> bool:
        """Return True when the condition passes for the given context."""

        return bool(self.evaluator(context))

    @classmethod
    def from_expression(
        cls, name: str, expression: str, description: str | None = None
    ) -> "PolicyCondition":
        """Create a condition compiled from the condition language expression."""

        compiler = ConditionLanguage(expression)
        return cls(
            name=name,
            description=description or expression,
            evaluator=compiler.evaluator,
        )


@dataclass
class EnforcementAction:
    """Action that will be dispatched through an enforcement channel."""

    action_id: str
    channel: str
    payload_builder: PayloadBuilder
    fallback_channel: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dynamic_callback: Optional[DynamicCallback] = None

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build channel payload from an event context."""

        return self.payload_builder(context)

    def apply_callback(self, payload: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        if not self.dynamic_callback:
            return result
        callback_result = self.dynamic_callback(payload, result)
        return callback_result or result


@dataclass
class Role:
    """Role definition for role-aware, autonomous agents."""

    role_id: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class AuthorityFootprint:
    """Snapshot describing how a role is staffed and governed."""

    role_id: str
    capabilities: List[str]
    tags: List[str]
    agents: List[str]
    policies: List[str]
    minimum_trust: float = 0.0

    def status(self) -> str:
        if not self.agents and not self.policies:
            return "unassigned"
        if not self.agents:
            return "unstaffed"
        if not self.policies:
            return "unbounded"
        return "active"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "capabilities": self.capabilities,
            "tags": self.tags,
            "agents": self.agents,
            "policies": self.policies,
            "minimum_trust": self.minimum_trust,
            "status": self.status(),
        }


@dataclass
class PolicyRotation:
    """Time-based rotation between policy versions or alternates."""

    alternate_policy_id: str
    interval_minutes: int
    last_rotated_at: Optional[datetime] = None

    def should_rotate(self, now: datetime) -> bool:
        if self.last_rotated_at is None:
            return False
        return now - self.last_rotated_at >= timedelta(minutes=self.interval_minutes)

    def mark_rotated(self, now: datetime) -> None:
        self.last_rotated_at = now


@dataclass
class Policy:
    """Governance policy composed of conditions and enforcement actions."""

    policy_id: str
    description: str
    conditions: List[PolicyCondition]
    actions: List[EnforcementAction]
    severity: str = "medium"
    tags: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    family: Optional[str] = None
    parent_policy_id: Optional[str] = None
    active_from: Optional[datetime] = None
    active_until: Optional[datetime] = None
    rotation: Optional[PolicyRotation] = None
    minimum_trust: float = 0.0

    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Return True when all conditions pass for the given context."""

        passed, _ = self.evaluate_conditions(context)
        return passed

    def evaluate_conditions(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Evaluate all conditions and return a tuple of (passed, failures)."""

        failures: List[str] = []
        for condition in self.conditions:
            if not condition.check(context):
                failures.append(condition.name)
        return not failures, failures

    def is_active(self, now: Optional[datetime] = None) -> bool:
        current = now or datetime.now(timezone.utc)
        if self.active_from and current < self.active_from:
            return False
        if self.active_until and current > self.active_until:
            return False
        return True


@dataclass
class Agent:
    """Responsible actor capable of executing enforcement actions."""

    agent_id: str
    capabilities: List[str]
    tags: List[str] = field(default_factory=list)
    trust: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    kind: str = "general"  # offline, service, self-healing, role-specific, general
    role: Optional[str] = None
    offline_ready: bool = False
    self_healing_capable: bool = False


class AgentMesh:
    """Mesh that keeps offline, service, self-healing, and role agents aligned."""

    def __init__(self, agents: Iterable[Agent] | None = None) -> None:
        self.agents: Dict[str, Agent] = {}
        self.offline_agents: Dict[str, Agent] = {}
        self.local_services: Dict[str, Agent] = {}
        self.self_healing: Dict[str, Agent] = {}
        self.role_agents: Dict[str, Dict[str, Agent]] = {}
        for agent in agents or []:
            self.register(agent)

    def register(self, agent: Agent) -> None:
        self.agents[agent.agent_id] = agent
        if agent.offline_ready:
            self.offline_agents[agent.agent_id] = agent
        if agent.kind == "service":
            self.local_services[agent.agent_id] = agent
        if agent.self_healing_capable or agent.kind == "self-healing":
            self.self_healing[agent.agent_id] = agent
        if agent.role:
            self.role_agents.setdefault(agent.role, {})[agent.agent_id] = agent

    def candidates(self, policy: Policy, roles: Dict[str, Role]) -> List[Agent]:
        ordered: List[Agent] = []
        for role_id in policy.roles:
            ordered.extend(self.role_agents.get(role_id, {}).values())
        ordered.extend(self.local_services.values())
        ordered.extend(self.self_healing.values())
        ordered.extend(self.offline_agents.values())
        ordered.extend(self.agents.values())
        return self._filter_candidates(ordered, policy, roles)

    def _filter_candidates(self, agents: Iterable[Agent], policy: Policy, roles: Dict[str, Role]) -> List[Agent]:
        seen: set[str] = set()
        filtered: List[Agent] = []
        for agent in agents:
            if agent.agent_id in seen:
                continue
            if policy.tags and not set(agent.tags) & set(policy.tags):
                continue
            if policy.roles and agent.role and agent.role in policy.roles:
                seen.add(agent.agent_id)
                filtered.append(agent)
                continue
            if not policy.roles:
                seen.add(agent.agent_id)
                filtered.append(agent)
                continue
            role_def = roles.get(agent.role or "")
            if role_def and (set(role_def.tags) & set(policy.tags) or set(role_def.capabilities) & set(agent.capabilities)):
                seen.add(agent.agent_id)
                filtered.append(agent)
        return filtered


class GovernanceRouter:
    """Routes policies to aligned agents and enforcement channels."""

    def __init__(
        self,
        policies: Iterable[Policy] | None = None,
        agents: Iterable[Agent] | None = None,
        channels: Dict[str, ChannelHandler] | None = None,
        roles: Iterable[Role] | None = None,
    ) -> None:
        self.policies: Dict[str, Policy] = {policy.policy_id: policy for policy in policies or []}
        self.policy_versions: Dict[str, Dict[str, Policy]] = {}
        self.roles: Dict[str, Role] = {role.role_id: role for role in roles or []}
        self.mesh = AgentMesh(agents)
        self.channels: Dict[str, ChannelHandler] = channels.copy() if channels else {}
        self.enforcement_events: List[Dict[str, Any]] = []
        self.last_route_trace: List[Dict[str, Any]] = []

        # Provide a default channel that simply records the payload for observability.
        if "record" not in self.channels:
            self.channels["record"] = self._record_channel

        for policy in policies or []:
            self._add_policy_version(policy)

    def register_policy(self, policy: Policy) -> None:
        self.policies[policy.policy_id] = policy
        self._add_policy_version(policy)
        persistence.log_action("governance-router", "register_policy", {"policy_id": policy.policy_id, "version": policy.version})

    def register_agent(self, agent: Agent) -> None:
        self.mesh.register(agent)
        persistence.log_action("governance-router", "register_agent", {"agent_id": agent.agent_id, "kind": agent.kind})

    def register_channel(self, name: str, handler: ChannelHandler) -> None:
        self.channels[name] = handler
        persistence.log_action("governance-router", "register_channel", {"channel": name})

    def register_role(self, role: Role) -> None:
        self.roles[role.role_id] = role
        persistence.log_action("governance-router", "register_role", {"role_id": role.role_id})

    def authority_presence(self) -> Dict[str, Any]:
        """Summarize how authority is distributed across roles, agents, and policies."""

        footprints: List[AuthorityFootprint] = []
        for role_id, role in self.roles.items():
            agent_ids = sorted({agent.agent_id for agent in self.mesh.agents.values() if agent.role == role_id})
            policy_ids = sorted({policy.policy_id for policy in self.policies.values() if role_id in policy.roles})
            minimum_trust = min(
                (policy.minimum_trust for policy in self.policies.values() if role_id in policy.roles),
                default=0.0,
            )
            footprints.append(
                AuthorityFootprint(
                    role_id=role_id,
                    capabilities=list(role.capabilities),
                    tags=list(role.tags),
                    agents=agent_ids,
                    policies=policy_ids,
                    minimum_trust=minimum_trust,
                )
            )

        orphan_agents = sorted({agent.agent_id for agent in self.mesh.agents.values() if not agent.role})
        unscoped_policies = sorted({policy.policy_id for policy in self.policies.values() if not policy.roles})

        presence = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "roles": [footprint.as_dict() for footprint in footprints],
            "orphans": {"agents": orphan_agents, "policies": unscoped_policies},
            "counts": {
                "roles": len(footprints),
                "agents": len(self.mesh.agents),
                "policies": len(self.policies),
                "assigned_agents": sum(1 for footprint in footprints if footprint.agents),
            },
        }

        persistence.save_authority_presence(presence)
        return presence

    def route(self, context: Dict[str, Any], actor: str = "system") -> List[Dict[str, Any]]:
        """Route context through applicable policies and return enforcement results."""

        results: List[Dict[str, Any]] = []
        trace: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for policy in self._iter_effective_policies(now):
            policy_trace = {
                "policy_id": policy.policy_id,
                "version": policy.version,
                "severity": policy.severity,
                "status": "evaluating",
            }

            if not policy.is_active(now):
                policy_trace.update(status="inactive", reason="outside_active_window")
                persistence.log_action(
                    actor,
                    "route_skipped",
                    {
                        "policy_id": policy.policy_id,
                        "version": policy.version,
                        "reason": "inactive",
                    },
                )
                trace.append(policy_trace)
                continue

            passed, failures = policy.evaluate_conditions(context)
            if not passed:
                policy_trace.update(status="skipped", reason="conditions_failed", failures=failures)
                persistence.log_action(
                    actor,
                    "route_skipped",
                    {
                        "policy_id": policy.policy_id,
                        "version": policy.version,
                        "reason": "conditions_failed",
                        "failures": failures,
                    },
                )
                trace.append(policy_trace)
                continue

            try:
                agent = self._select_agent(policy)
            except RuntimeError as exc:
                policy_trace.update(status="failed", reason=str(exc))
                persistence.log_action(
                    actor,
                    "route_failed",
                    {
                        "policy_id": policy.policy_id,
                        "version": policy.version,
                        "reason": str(exc),
                    },
                )
                trace.append(policy_trace)
                continue

            policy_trace["agent"] = agent.agent_id
            policy_trace["status"] = "dispatched"
            policy_trace["actions"] = []
            for action in policy.actions:
                payload = action.build_payload({**context, "policy_id": policy.policy_id, "agent": agent.agent_id})
                result = self._dispatch(action, payload)
                result = action.apply_callback(payload, result)
                outcome = {
                    "policy_id": policy.policy_id,
                    "action_id": action.action_id,
                    "channel": result["channel"],
                    "agent": agent.agent_id,
                    "status": result.get("status", "sent"),
                    "details": result.get("details", {}),
                    "version": policy.version,
                }
                results.append(outcome)
                policy_trace["actions"].append(action.action_id)
                persistence.log_action(actor, "enforce", outcome)

            trace.append(policy_trace)

        if trace:
            persistence.save_snapshot({"context": context, "results": results, "trace": trace})
        self.last_route_trace = trace
        return results

    def policy_readiness(self) -> Dict[str, Any]:
        """Assess which policies can be executed and persist a readiness report.

        The report highlights policies that currently have no eligible agents that
        meet their trust requirements. It can be consumed by operational tooling
        to backfill staffing, adjust trust scores, or tune policy minimums.
        """

        now = datetime.now(timezone.utc)
        readiness: List[Dict[str, Any]] = []
        unroutable: List[str] = []

        for policy in self._iter_effective_policies(now):
            candidates = self.mesh.candidates(policy, self.roles)
            eligible = [agent for agent in candidates if agent.trust >= policy.minimum_trust]
            entry = {
                "policy_id": policy.policy_id,
                "version": policy.version,
                "roles": list(policy.roles),
                "tags": list(policy.tags),
                "minimum_trust": policy.minimum_trust,
                "eligible_agents": [agent.agent_id for agent in eligible],
                "candidate_count": len(eligible),
                "severity": policy.severity,
            }
            readiness.append(entry)
            if not eligible:
                unroutable.append(policy.policy_id)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "policies": readiness,
            "unroutable": unroutable,
            "counts": {"policies": len(readiness), "unroutable": len(unroutable)},
        }

        persistence.save_policy_readiness(report)
        return report

    def _iter_effective_policies(self, now: datetime) -> Iterable[Policy]:
        for versions in self.policy_versions.values():
            latest = self._select_latest_version(versions)
            resolved = self._resolve_inheritance(latest)
            yield self._apply_rotation(resolved, now)

    def _select_agent(self, policy: Policy) -> Agent:
        """Select an agent aligned with policy tags, roles, or fallback to trusted actor."""

        candidates = self.mesh.candidates(policy, self.roles)
        if policy.minimum_trust > 0:
            candidates = [agent for agent in candidates if agent.trust >= policy.minimum_trust]
        if not candidates:
            candidates = [agent for agent in self.mesh.agents.values() if agent.trust >= policy.minimum_trust]
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

    def _add_policy_version(self, policy: Policy) -> None:
        family = policy.family or policy.policy_id
        self.policy_versions.setdefault(family, {})[policy.version] = policy

    def _select_latest_version(self, policies: Dict[str, Policy]) -> Policy:
        def version_key(version: str) -> List[int]:
            return [int(part) for part in version.split(".") if part.isdigit()]

        latest_version = sorted(policies.keys(), key=version_key, reverse=True)[0]
        return policies[latest_version]

    def _resolve_inheritance(self, policy: Policy) -> Policy:
        if not policy.parent_policy_id or policy.parent_policy_id not in self.policies:
            return policy
        parent = self._resolve_inheritance(self.policies[policy.parent_policy_id])
        merged = deepcopy(parent)
        merged.policy_id = policy.policy_id
        merged.version = policy.version
        merged.description = policy.description
        merged.severity = policy.severity
        merged.tags = list(dict.fromkeys(parent.tags + policy.tags))
        merged.roles = list(dict.fromkeys(parent.roles + policy.roles))
        merged.conditions = parent.conditions + policy.conditions
        merged.actions = parent.actions + policy.actions
        merged.rotation = policy.rotation or parent.rotation
        merged.active_from = policy.active_from or parent.active_from
        merged.active_until = policy.active_until or parent.active_until
        return merged

    def _apply_rotation(self, policy: Policy, now: datetime) -> Policy:
        if not policy.rotation:
            return policy
        rotation = policy.rotation
        if rotation.should_rotate(now) and rotation.alternate_policy_id in self.policies:
            rotation.mark_rotated(now)
            return self._resolve_inheritance(self.policies[rotation.alternate_policy_id])
        if rotation.last_rotated_at is None:
            rotation.mark_rotated(now)
        return policy

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


def expression_condition(name: str, expression: str, description: str | None = None) -> PolicyCondition:
    """Create a condition using the declarative condition language."""

    return PolicyCondition.from_expression(name=name, expression=expression, description=description)


def rotation(alternate_policy_id: str, interval_minutes: int) -> PolicyRotation:
    """Helper to construct timed rotations between policy variants."""

    return PolicyRotation(alternate_policy_id=alternate_policy_id, interval_minutes=interval_minutes)
