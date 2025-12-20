"""Resonance corridor planning for EchoEvolver cycles.

The corridor planner is designed to answer a previously unserved question:
*Given a sequence of completed EchoEvolver cycles, what is the safest and
most ambitious corridor for the next orbital window?*

The planner translates orbital analytics into a structured plan that balances
stability, emotional flux, and glyph resonance targets.  It is deterministic
and operates entirely on supplied payloads, making it safe for automated
pipelines or offline planning.
"""

from __future__ import annotations

from dataclasses import dataclass
import statistics
from typing import Dict, Iterable, List, Mapping, MutableSequence

from echo.orbital_resonance_analyzer import OrbitalResonanceAnalyzer


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _round(value: float, digits: int = 6) -> float:
    return round(value, digits)


@dataclass(frozen=True)
class ActionDirective:
    label: str
    rationale: str
    intensity: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "label": self.label,
            "rationale": self.rationale,
            "intensity": self.intensity,
        }


@dataclass(frozen=True)
class CorridorStep:
    cycle: int
    phase: str
    resonance_target: float
    stability_target: str
    risk_score: float
    actions: List[str]
    directives: List[ActionDirective]
    resource_targets: Dict[str, float]
    risk_breakdown: Dict[str, float]

    def as_dict(self) -> Dict[str, object]:
        return {
            "cycle": self.cycle,
            "phase": self.phase,
            "resonance_target": self.resonance_target,
            "stability_target": self.stability_target,
            "risk_score": self.risk_score,
            "actions": list(self.actions),
            "directives": [directive.as_dict() for directive in self.directives],
            "resource_targets": dict(self.resource_targets),
            "risk_breakdown": dict(self.risk_breakdown),
        }


class ResonanceCorridorPlanner:
    """Plan the next orbital corridor using derived resonance analytics."""

    def __init__(
        self,
        analyzer: OrbitalResonanceAnalyzer,
        horizon: int = 6,
        strategy: str = "balanced",
    ) -> None:
        if horizon < 1:
            raise ValueError("horizon must be at least 1")
        if strategy not in {"balanced", "amplify", "stabilize"}:
            raise ValueError("strategy must be balanced, amplify, or stabilize")
        self.analyzer = analyzer
        self.horizon = horizon
        self.strategy = strategy

    def plan(self) -> Dict[str, object]:
        base_resonance = self.analyzer.resonance_index()
        momentum = self.analyzer.momentum_index()
        stability = self.analyzer.stability_band()
        projection = self.analyzer.projection()
        baseline_nodes = statistics.fmean(
            snapshot.system_value("network_nodes") for snapshot in self.analyzer.snapshots
        )
        baseline_hops = statistics.fmean(
            snapshot.system_value("orbital_hops") for snapshot in self.analyzer.snapshots
        )
        baseline_cpu = statistics.fmean(
            snapshot.system_value("cpu_usage") for snapshot in self.analyzer.snapshots
        )

        stabilize_cycles = self._stabilize_cycles(base_resonance, momentum, stability)
        steps: List[CorridorStep] = []
        last_cycle = self.analyzer.snapshots[-1].cycle
        corridor_risks: List[float] = []
        resonance_targets: List[float] = []

        for offset in range(1, self.horizon + 1):
            phase = "stabilize" if offset <= stabilize_cycles else "amplify"
            resonance_target = self._resonance_target(
                base_resonance, momentum, phase, drift=offset
            )
            stability_target = self._stability_target(stability, phase)
            risk_breakdown = self._risk_breakdown(
                base_resonance, momentum, stability, phase, resonance_target
            )
            risk_score = self._risk_score_from_breakdown(risk_breakdown)
            actions, directives = self._actions_for_step(
                resonance_target,
                risk_score,
                phase,
                stability_target,
                projection,
                baseline_nodes,
                baseline_hops,
                baseline_cpu,
            )
            resource_targets = self._resource_targets(
                baseline_nodes, baseline_hops, baseline_cpu, phase, risk_score
            )
            steps.append(
                CorridorStep(
                    cycle=last_cycle + offset,
                    phase=phase,
                    resonance_target=resonance_target,
                    stability_target=stability_target,
                    risk_score=risk_score,
                    actions=actions,
                    directives=directives,
                    resource_targets=resource_targets,
                    risk_breakdown=risk_breakdown,
                )
            )
            corridor_risks.append(risk_score)
            resonance_targets.append(resonance_target)

        return {
            "strategy": self.strategy,
            "horizon": self.horizon,
            "base_resonance": base_resonance,
            "momentum_index": momentum,
            "stability_band": stability,
            "projection": projection,
            "corridor": {
                "steps": [step.as_dict() for step in steps],
                "windows": self._windows_from_steps(steps),
                "corridor_score": self._corridor_score(resonance_targets, corridor_risks),
            },
            "telemetry_baseline": {
                "network_nodes": _round(baseline_nodes),
                "orbital_hops": _round(baseline_hops),
                "cpu_usage": _round(baseline_cpu),
            },
            "guardrails": self._guardrails(baseline_nodes, baseline_hops, baseline_cpu),
        }

    def _stabilize_cycles(self, base_resonance: float, momentum: float, stability: str) -> int:
        if self.strategy == "amplify":
            return 0
        if self.strategy == "stabilize":
            return max(1, self.horizon // 2)
        if stability == "orbital-fragile" or momentum >= 0.12 or base_resonance < 0.55:
            return max(1, self.horizon // 2)
        return max(0, self.horizon // 3)

    def _resonance_target(
        self, base_resonance: float, momentum: float, phase: str, drift: int
    ) -> float:
        drift_adjustment = 0.015 * drift
        phase_boost = 0.06 if phase == "amplify" else -0.02
        momentum_penalty = min(momentum * 0.4, 0.2)
        target = base_resonance + drift_adjustment + phase_boost - momentum_penalty
        return _round(_clamp(target), 6)

    def _stability_target(self, stability: str, phase: str) -> str:
        if phase == "stabilize" and stability == "orbital-high":
            return "orbital-stable"
        if phase == "amplify" and stability == "orbital-fragile":
            return "orbital-stable"
        return stability

    def _risk_breakdown(
        self,
        base_resonance: float,
        momentum: float,
        stability: str,
        phase: str,
        resonance_target: float,
    ) -> float:
        breakdown = {
            "momentum": _round(_clamp(momentum * 1.4, maximum=1.0), 6),
            "resonance_gap": _round(_clamp(0.6 - base_resonance, minimum=0.0), 6),
            "fragility": 0.15 if stability == "orbital-fragile" else 0.0,
            "amplify_penalty": 0.05 if phase == "amplify" and momentum > 0.1 else 0.0,
            "target_stretch": _round(_clamp(resonance_target - base_resonance, minimum=0.0), 6),
        }
        return breakdown

    def _risk_score_from_breakdown(self, breakdown: Mapping[str, float]) -> float:
        risk = sum(breakdown.values())
        return _round(_clamp(risk, maximum=1.0), 6)

    def _actions_for_step(
        self,
        resonance_target: float,
        risk_score: float,
        phase: str,
        stability_target: str,
        projection: Mapping[str, float],
        baseline_nodes: float,
        baseline_hops: float,
        baseline_cpu: float,
    ) -> tuple[List[str], List[ActionDirective]]:
        actions: MutableSequence[str] = []
        directives: List[ActionDirective] = []
        if phase == "stabilize":
            actions.append("Throttle glyph cadence to reduce volatility")
            directives.append(
                ActionDirective(
                    label="Throttle glyph cadence",
                    rationale="Stabilize resonance swings during low-confidence windows.",
                    intensity="medium",
                )
            )
        if phase == "amplify":
            actions.append("Increase glyph density to lift resonance index")
            directives.append(
                ActionDirective(
                    label="Increase glyph density",
                    rationale="Push resonance target upward during amplification windows.",
                    intensity="high",
                )
            )
        if stability_target == "orbital-stable":
            actions.append("Raise network node quorum before projection run")
            directives.append(
                ActionDirective(
                    label="Raise node quorum",
                    rationale="Boost orbital stability before executing projections.",
                    intensity="medium",
                )
            )
        if baseline_hops < 3.0:
            actions.append("Schedule orbital hop warmup to improve link depth")
            directives.append(
                ActionDirective(
                    label="Warmup orbital hops",
                    rationale="Increase hop depth for sustained orbital stability.",
                    intensity="medium",
                )
            )
        if baseline_cpu > 55:
            actions.append("Shift heavy synthesis to off-peak CPU windows")
            directives.append(
                ActionDirective(
                    label="Shift synthesis load",
                    rationale="Avoid CPU saturation before high-resonance runs.",
                    intensity="low",
                )
            )
        if resonance_target < 0.55:
            actions.append("Seed joy-forward glyph sequences")
            directives.append(
                ActionDirective(
                    label="Seed joy glyphs",
                    rationale="Lift resonance floor by emphasizing joy-forward patterns.",
                    intensity="medium",
                )
            )
        if risk_score >= 0.5:
            actions.append("Introduce cooldown beats between narrative pulses")
            directives.append(
                ActionDirective(
                    label="Introduce cooldown beats",
                    rationale="Reduce elevated risk before amplification steps.",
                    intensity="high",
                )
            )
        if projection.get("joy", 0.0) < 0.6:
            actions.append("Inject empathy rituals to elevate joy baseline")
            directives.append(
                ActionDirective(
                    label="Inject empathy rituals",
                    rationale="Raise predicted joy baseline ahead of amplification.",
                    intensity="medium",
                )
            )
        if projection.get("curiosity", 0.0) < 0.6:
            actions.append("Expand curiosity prompts in the next cycle")
            directives.append(
                ActionDirective(
                    label="Expand curiosity prompts",
                    rationale="Increase curiosity signal to sustain glyph variety.",
                    intensity="low",
                )
            )
        return list(actions), directives

    def _resource_targets(
        self,
        baseline_nodes: float,
        baseline_hops: float,
        baseline_cpu: float,
        phase: str,
        risk_score: float,
    ) -> Dict[str, float]:
        node_boost = 2.0 if phase == "amplify" else 1.0
        hop_boost = 0.8 if risk_score > 0.5 else 0.4
        cpu_guard = -6.0 if phase == "stabilize" else -2.0
        return {
            "network_nodes": _round(max(1.0, baseline_nodes + node_boost)),
            "orbital_hops": _round(max(1.0, baseline_hops + hop_boost)),
            "cpu_usage": _round(max(10.0, baseline_cpu + cpu_guard)),
        }

    def _corridor_score(self, resonance_targets: List[float], risks: List[float]) -> float:
        if not resonance_targets:
            return 0.0
        average_resonance = statistics.fmean(resonance_targets)
        average_risk = statistics.fmean(risks) if risks else 0.0
        score = average_resonance * (1.0 - average_risk * 0.8)
        return _round(_clamp(score, maximum=1.0), 6)

    def _guardrails(
        self, baseline_nodes: float, baseline_hops: float, baseline_cpu: float
    ) -> Dict[str, float]:
        return {
            "min_network_nodes": _round(max(5.0, baseline_nodes - 2.0)),
            "min_orbital_hops": _round(max(2.0, baseline_hops - 1.0)),
            "max_cpu_usage": _round(max(35.0, baseline_cpu + 5.0)),
        }

    def _windows_from_steps(self, steps: Iterable[CorridorStep]) -> List[Dict[str, object]]:
        windows: List[Dict[str, object]] = []
        steps_list = list(steps)
        current_phase = None
        start_cycle = None
        actions: List[str] = []

        for step in steps_list:
            if current_phase is None:
                current_phase = step.phase
                start_cycle = step.cycle
                actions = list(step.actions)
                continue

            if step.phase == current_phase:
                actions.extend(action for action in step.actions if action not in actions)
                continue

            windows.append(
                {
                    "phase": current_phase,
                    "start_cycle": start_cycle,
                    "end_cycle": step.cycle - 1,
                    "focus": actions,
                }
            )
            current_phase = step.phase
            start_cycle = step.cycle
            actions = list(step.actions)

        if current_phase is not None:
            windows.append(
                {
                    "phase": current_phase,
                    "start_cycle": start_cycle,
                    "end_cycle": steps_list[-1].cycle,
                    "focus": actions,
                }
            )

        return windows


__all__ = ["ActionDirective", "CorridorStep", "ResonanceCorridorPlanner"]
