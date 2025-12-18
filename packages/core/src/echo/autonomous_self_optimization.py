"""Autonomous optimization, negotiation, offline runtime, and qualification primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Callable, Dict, List, Mapping, MutableMapping, Sequence


@dataclass
class PolicyBundle:
    """A self-contained policy bundle with live optimization metadata."""

    name: str
    version: str
    policies: Dict[str, float]
    convergence_score: float = 0.0
    streaming_threshold: float = 0.5
    convergence_history: List[float] = field(default_factory=list)

    def update_scores(self, observed: float, *, streaming_health: float) -> None:
        """Update convergence and streaming thresholds based on new observations."""

        self.convergence_history.append(observed)
        self.convergence_score = mean(self.convergence_history)
        adjustment = 0.05 if streaming_health > self.streaming_threshold else -0.05
        self.streaming_threshold = max(0.1, min(0.9, self.streaming_threshold + adjustment))


@dataclass
class OptimizationOutcome:
    """Summary of a completed self-optimization cycle."""

    policy_bundle: PolicyBundle
    cycle: int
    updated_at: datetime
    convergence_delta: float
    streaming_threshold: float
    notes: List[str] = field(default_factory=list)


class AutonomousSelfOptimizer:
    """Continuously improves policy bundles using online metrics."""

    def __init__(self) -> None:
        self._cycle = 0
        self._last_convergence: float | None = None

    def optimize(
        self,
        policy_bundle: PolicyBundle,
        *,
        observed_convergence: float,
        streaming_health: float,
        hints: Sequence[str] | None = None,
    ) -> OptimizationOutcome:
        """Advance the optimization cycle with new telemetry."""

        before = policy_bundle.convergence_score
        policy_bundle.update_scores(observed_convergence, streaming_health=streaming_health)
        self._cycle += 1

        notes: list[str] = [
            f"ingested_observation={observed_convergence:.3f}",
            f"streaming_health={streaming_health:.3f}",
        ]
        if hints:
            notes.extend(hints)

        if self._last_convergence is not None:
            delta = policy_bundle.convergence_score - self._last_convergence
            notes.append(f"convergence_delta={delta:.3f}")
        self._last_convergence = policy_bundle.convergence_score

        return OptimizationOutcome(
            policy_bundle=policy_bundle,
            cycle=self._cycle,
            updated_at=datetime.now(timezone.utc),
            convergence_delta=policy_bundle.convergence_score - before,
            streaming_threshold=policy_bundle.streaming_threshold,
            notes=notes,
        )


@dataclass
class AgentPerspective:
    """Perspective offered by an agent for a shared task."""

    agent_id: str
    priority: float
    insights: List[str] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)


@dataclass
class NegotiatedDecision:
    """Result of a cross-agent negotiation."""

    task: str
    resolved: bool
    selected_agent: str | None
    merged_insights: List[str]
    conflict_points: List[str]


class CrossAgentNegotiationLayer:
    """Lightweight negotiation coordinator for multiple agents."""

    def __init__(self) -> None:
        self._history: list[NegotiatedDecision] = []

    @property
    def history(self) -> Sequence[NegotiatedDecision]:
        return tuple(self._history)

    def negotiate(self, task: str, perspectives: Sequence[AgentPerspective]) -> NegotiatedDecision:
        """Resolve a task by prioritising convergent agent perspectives."""

        if not perspectives:
            decision = NegotiatedDecision(task, False, None, [], ["no participants"])
            self._history.append(decision)
            return decision

        sorted_agents = sorted(perspectives, key=lambda p: p.priority, reverse=True)
        merged_insights: list[str] = []
        conflict_points: list[str] = []
        winning_agent = sorted_agents[0]

        for perspective in sorted_agents:
            merged_insights.extend(perspective.insights)
            conflict_points.extend(perspective.objections)

        conflict_points = list(dict.fromkeys(conflict_points))
        merged_insights = list(dict.fromkeys(merged_insights))
        resolved = len(conflict_points) == 0 or winning_agent.priority >= 0.5

        decision = NegotiatedDecision(
            task=task,
            resolved=resolved,
            selected_agent=winning_agent.agent_id if resolved else None,
            merged_insights=merged_insights,
            conflict_points=conflict_points,
        )
        self._history.append(decision)
        return decision


@dataclass
class OfflineTask:
    """Task scheduled for the offline runtime."""

    name: str
    payload: Mapping[str, object]
    requires_network: bool = False
    executed: bool = False
    result: Mapping[str, object] | None = None
    blocked_reason: str | None = None


@dataclass
class RegisteredCapability:
    """Capability metadata registered with the local runtime."""

    handler: Callable[[Mapping[str, object]], Mapping[str, object] | object]
    offline_ready: bool = True
    description: str | None = None


class LocalDeviceRuntime:
    """Offline-first runtime that can execute tasks without network access."""

    def __init__(self) -> None:
        self._capabilities: MutableMapping[str, RegisteredCapability] = {}
        self._task_queue: list[OfflineTask] = []
        self._completed: list[OfflineTask] = []

    def register_capability(
        self,
        name: str,
        handler: Callable[[Mapping[str, object]], Mapping[str, object] | object],
        *,
        offline_ready: bool = True,
        description: str | None = None,
    ) -> None:
        self._capabilities[name] = RegisteredCapability(
            handler=handler, offline_ready=offline_ready, description=description
        )

    def submit_task(self, task: OfflineTask) -> None:
        self._task_queue.append(task)

    def run(self, *, network_available: bool = False) -> list[OfflineTask]:
        """Execute queued tasks, optionally including those needing the network."""

        remaining: list[OfflineTask] = []
        for task in self._task_queue:
            capability = self._capabilities.get(task.name)

            if capability is None:
                task.blocked_reason = "unregistered_capability"
                remaining.append(task)
                continue

            if task.requires_network and not network_available:
                task.blocked_reason = "network_unavailable"
                remaining.append(task)
                continue

            if not capability.offline_ready and not network_available:
                task.blocked_reason = "capability_offline_disabled"
                remaining.append(task)
                continue

            try:
                result = capability.handler(task.payload)
            except Exception as exc:  # pragma: no cover - defensive path validated in tests
                task.blocked_reason = "handler_error"
                task.result = {"error": str(exc)}
                remaining.append(task)
                continue

            task.executed = True
            task.blocked_reason = None
            task.result = result if isinstance(result, Mapping) else {"result": result}
            self._completed.append(task)

        self._task_queue = remaining
        return list(self._completed)

    @property
    def pending(self) -> Sequence[OfflineTask]:
        return tuple(self._task_queue)

    @property
    def completed(self) -> Sequence[OfflineTask]:
        return tuple(self._completed)

    def snapshot(self) -> Mapping[str, object]:
        """Summarise offline execution state for dashboards and audits."""

        pending_network = [task.name for task in self._task_queue if task.requires_network]
        return {
            "pending": [task.name for task in self._task_queue],
            "pending_requires_network": pending_network,
            "pending_details": [
                {
                    "name": task.name,
                    "requires_network": task.requires_network,
                    "blocked_reason": task.blocked_reason,
                }
                for task in self._task_queue
            ],
            "completed": [
                {
                    "name": task.name,
                    "requires_network": task.requires_network,
                    "executed": task.executed,
                }
                for task in self._completed
            ],
            "capabilities": {
                name: {
                    "offline_ready": capability.offline_ready,
                    "description": capability.description,
                }
                for name, capability in self._capabilities.items()
            },
        }


@dataclass
class LeadProfile:
    """Structured profile for a broker or real-estate lead."""

    name: str
    credit_score: int
    liquidity: float
    jurisdictions: Sequence[str]
    use_case: str
    intents: Sequence[str]


@dataclass
class QualificationResult:
    """Outcome from the broker/real-estate qualification module."""

    lead: LeadProfile
    risk_flags: List[str]
    qualification_score: float
    recommended_bundle: str


class RealEstateQualificationModule:
    """Scores and qualifies real-estate or brokerage leads."""

    def __init__(self, *, policy_bundles: Mapping[str, PolicyBundle]):
        self._bundles = dict(policy_bundles)

    def qualify(self, lead: LeadProfile) -> QualificationResult:
        flags: list[str] = []
        if lead.credit_score < 650:
            flags.append("low_credit")
        if lead.liquidity < 25000:
            flags.append("limited_liquidity")
        if "high_risk" in lead.intents:
            flags.append("high_risk_intent")

        base_score = lead.credit_score / 850
        liquidity_bonus = min(1.0, lead.liquidity / 500000)
        intent_bonus = 0.1 if "buy" in lead.intents else 0.0
        jurisdiction_factor = 1.0 if "US" in lead.jurisdictions else 0.85

        score = max(
            0.0,
            min(1.0, base_score * jurisdiction_factor + liquidity_bonus + intent_bonus),
        )

        recommended_bundle = self._select_bundle(score)
        return QualificationResult(
            lead=lead,
            risk_flags=flags,
            qualification_score=score,
            recommended_bundle=recommended_bundle,
        )

    def _select_bundle(self, score: float) -> str:
        ranked = sorted(self._bundles.values(), key=lambda b: b.convergence_score, reverse=True)
        if not ranked:
            return "baseline"
        for bundle in ranked:
            if score >= bundle.streaming_threshold:
                return bundle.name
        return ranked[-1].name
