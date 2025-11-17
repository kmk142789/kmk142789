"""Progressively more complex analytical helpers for the Echo toolkit."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from math import isfinite
from statistics import pstdev
from typing import Iterable, Mapping, Sequence

__all__ = [
    "generate_numeric_intelligence",
    "analyze_text_corpus",
    "simulate_delivery_timeline",
    "evaluate_strategy_matrix",
    "forecast_operational_resilience",
    "plan_capacity_allocation",
    "simulate_portfolio_outcomes",
    "generate_innovation_radar",
    "generate_innovation_orbit",
    "progressive_complexity_suite",
    "complexity_evolution_series",
    "assess_alignment_signals",
    "evaluate_operational_readiness",
    "forecast_portfolio_throughput",
    "generate_signal_snapshot",
    "synthesize_operational_dashboard",
    "build_complexity_checkpoint",
    "compose_complexity_journey",
    "orchestrate_complexity_summit",
    "orchestrate_complexity_progression",
    "orchestrate_complexity_constellation",
    "execute_complexity_cascade",
    "execute_feature_escalation",
    "construct_complexity_foundation",
    "simulate_complexity_orbit",
    "orchestrate_complexity_supercluster",
    "synthesize_complexity_continuum",
    "orchestrate_complexity_hyperdrive",
    "generate_complexity_observatory",
    "orchestrate_complexity_metaweb",
    "orchestrate_complexity_multiverse",
    "CascadeStage",
]


@dataclass(frozen=True)
class TimelineMilestone:
    """Simple representation of a delivery milestone."""

    name: str
    duration_days: float
    confidence: float

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "TimelineMilestone":
        try:
            name = str(data["name"]).strip()
            duration = float(data["duration"])
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("invalid milestone specification") from exc
        if not name:
            raise ValueError("milestone name cannot be empty")
        if duration <= 0:
            raise ValueError("milestone duration must be positive")
        confidence = float(data.get("confidence", 0.8))
        if not 0 < confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return cls(name=name, duration_days=duration, confidence=confidence)


@dataclass(frozen=True)
class StrategyOption:
    """Weighted strategy evaluation option."""

    name: str
    metrics: Mapping[str, float]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "StrategyOption":
        try:
            name = str(data["name"]).strip()
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError("strategy option requires a name") from exc
        if not name:
            raise ValueError("strategy option name cannot be empty")
        metrics: dict[str, float] = {}
        for key, value in data.items():
            if key == "name":
                continue
            try:
                metrics[key] = float(value)
            except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
                raise ValueError(f"metric '{key}' must be numeric") from exc
        if not metrics:
            raise ValueError("strategy option requires at least one metric")
        return cls(name=name, metrics=metrics)


@dataclass(frozen=True)
class ResilienceEvent:
    """Representation of an operational resilience stressor."""

    name: str
    likelihood: float
    impact_hours: float
    recovery_hours: float
    detection_hours: float = 4.0
    criticality: str = "medium"

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "ResilienceEvent":
        try:
            name = str(data["name"]).strip()
            likelihood = float(data.get("likelihood", 0.3))
            impact = float(data["impact_hours"])
            recovery = float(data.get("recovery_hours", 6.0))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid resilience event specification") from exc
        detection = float(data.get("detection_hours", 4.0))
        criticality = str(data.get("criticality", "medium")).lower()
        if not name:
            raise ValueError("event name cannot be empty")
        if not 0 < likelihood <= 1:
            raise ValueError("likelihood must be between 0 and 1")
        if min(impact, recovery, detection) <= 0:
            raise ValueError("time-based attributes must be positive")
        return cls(
            name=name,
            likelihood=likelihood,
            impact_hours=impact,
            recovery_hours=recovery,
            detection_hours=detection,
            criticality=criticality,
        )

    @property
    def total_hours(self) -> float:
        return self.impact_hours + self.recovery_hours + self.detection_hours
class WorkItem:
    """Represents a scoped piece of work used for capacity planning."""

    name: str
    team: str
    effort_hours: float
    priority: int = 3

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "WorkItem":
        try:
            name = str(data["name"]).strip()
            team = str(data["team"]).strip()
            effort = float(data["effort"])
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("invalid work item specification") from exc
        if not name or not team:
            raise ValueError("work item name and team must be provided")
        if effort <= 0:
            raise ValueError("work item effort must be positive")
        priority = int(data.get("priority", 3))
        if priority < 1:
            raise ValueError("priority must be a positive integer")
        return cls(name=name, team=team, effort_hours=effort, priority=priority)


@dataclass(frozen=True)
class PortfolioInitiative:
    """Container describing a multi-milestone initiative within a portfolio."""

    name: str
    milestones: Sequence[TimelineMilestone]
    weight: float = 1.0
    value: float = 1.0
    start: datetime | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "PortfolioInitiative":
        try:
            name = str(data["name"]).strip()
        except (KeyError, TypeError) as exc:  # pragma: no cover - defensive
            raise ValueError("initiative name is required") from exc
        if not name:
            raise ValueError("initiative name cannot be empty")
        raw_milestones = data.get("milestones")
        if not isinstance(raw_milestones, Sequence) or not raw_milestones:
            raise ValueError("initiative milestones must be a non-empty sequence")
        milestones = [
            TimelineMilestone.from_mapping(milestone) if not isinstance(milestone, TimelineMilestone) else milestone
            for milestone in raw_milestones
        ]
        weight = float(data.get("weight", 1.0))
        if weight <= 0:
            raise ValueError("initiative weight must be positive")
        value = float(data.get("value", 1.0))
        start_value = data.get("start")
        start_dt: datetime | None = None
        if isinstance(start_value, datetime):
            start_dt = _normalise_datetime(start_value)
        elif isinstance(start_value, str) and start_value.strip():
            start_dt = _parse_iso_timestamp(start_value)
        return cls(name=name, milestones=milestones, weight=weight, value=value, start=start_dt)


@dataclass(frozen=True)
class InnovationNode:
    """Representation of a frontier innovation signal."""

    name: str
    novelty: float
    adoption: float
    risk: float
    investment: float
    horizon: str = "core"
    signal_strength: float = 0.5

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "InnovationNode":
        try:
            name = str(data["name"]).strip()
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError("innovation node requires a name") from exc
        if not name:
            raise ValueError("innovation node name cannot be empty")
        novelty = float(data.get("novelty", 0.5))
        adoption = float(data.get("adoption", 0.5))
        risk = float(data.get("risk", 0.4))
        investment = float(data.get("investment", 1.0))
        signal = float(data.get("signal_strength", data.get("signal", 0.5)))
        for value, label in ((novelty, "novelty"), (adoption, "adoption"), (risk, "risk"), (signal, "signal_strength")):
            if not 0 <= value <= 1:
                raise ValueError(f"{label} must be between 0 and 1")
        if investment < 0:
            raise ValueError("investment must be non-negative")
        horizon = str(data.get("horizon", "core")).strip().lower() or "core"
        return cls(
            name=name,
            novelty=novelty,
            adoption=adoption,
            risk=risk,
            investment=investment,
            horizon=horizon,
            signal_strength=signal,
        )


@dataclass(frozen=True)
class CascadeStage:
    """Definition for a cascaded analytical stage."""

    name: str
    kind: str
    params: Mapping[str, object]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "CascadeStage":
        if not isinstance(data, Mapping):  # pragma: no cover - defensive
            raise ValueError("cascade stage must be a mapping")
        try:
            name = str(data.get("name", "")).strip() or "stage"
            kind = str(data["type"]).strip().lower()
        except KeyError as exc:
            raise ValueError("cascade stage requires a 'type' attribute") from exc
        params = data.get("params", {})
        if not isinstance(params, Mapping):
            raise ValueError("stage 'params' must be a mapping")
        return cls(name=name, kind=kind, params=dict(params))


def _normalise_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_timestamp(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ensure_datetime(value: object | None, fallback: datetime | None) -> datetime | None:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return _normalise_datetime(value)
    if isinstance(value, str) and value.strip():
        return _parse_iso_timestamp(value)
    raise ValueError("invalid datetime value supplied to cascade stage")


def generate_numeric_intelligence(count: int) -> dict[str, object]:
    """Generate a Fibonacci intelligence report with derivative metrics."""

    if count < 2:
        raise ValueError("count must be at least 2")

    sequence: list[int] = []
    a, b = 0, 1
    while len(sequence) < count:
        sequence.append(b)
        a, b = b, a + b

    derivatives = [sequence[i + 1] - sequence[i] for i in range(len(sequence) - 1)]
    ratios = [sequence[i + 1] / sequence[i] for i in range(len(sequence) - 1) if sequence[i] != 0]
    stats = {
        "total": sum(sequence),
        "mean": sum(sequence) / len(sequence),
        "max": max(sequence),
        "min": min(sequence),
        "even": len([n for n in sequence if n % 2 == 0]),
        "odd": len([n for n in sequence if n % 2 == 1]),
    }

    return {
        "sequence": sequence,
        "derivatives": derivatives,
        "ratio_trend": ratios,
        "stats": stats,
        "golden_ratio_estimate": ratios[-1] if ratios else None,
    }


def analyze_text_corpus(texts: Iterable[str]) -> dict[str, object]:
    """Analyse a corpus returning lexical and structural metrics."""

    normalised = [text.strip() for text in texts if text and text.strip()]
    if not normalised:
        raise ValueError("at least one non-empty document is required")

    total_chars = sum(len(text) for text in normalised)
    tokens: list[str] = []
    sentences = 0
    for text in normalised:
        for sentence in [s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]:
            sentences += 1
        for token in text.replace("\n", " ").split():
            clean = "".join(ch for ch in token if ch.isalnum()).lower()
            if clean:
                tokens.append(clean)

    token_counts = Counter(tokens)
    vocabulary = len(token_counts)
    total_words = len(tokens)
    avg_sentence_length = total_words / max(sentences, 1)
    lexical_density = vocabulary / max(total_words, 1)
    top_tokens = [
        {"token": token, "count": count}
        for token, count in token_counts.most_common(5)
    ]

    if avg_sentence_length < 12:
        readability = "concise"
    elif avg_sentence_length < 20:
        readability = "balanced"
    else:
        readability = "complex"

    return {
        "documents": len(normalised),
        "total_words": total_words,
        "total_characters": total_chars,
        "vocabulary": vocabulary,
        "lexical_density": round(lexical_density, 3),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "readability": readability,
        "top_tokens": top_tokens,
    }


def simulate_delivery_timeline(
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone],
    *,
    start: datetime | None = None,
) -> dict[str, object]:
    """Simulate a delivery timeline with confidence-aware buffers."""

    if not milestones:
        raise ValueError("at least one milestone is required")

    parsed: list[TimelineMilestone] = []
    for milestone in milestones:
        if isinstance(milestone, TimelineMilestone):
            parsed.append(milestone)
        else:
            parsed.append(TimelineMilestone.from_mapping(milestone))

    current = _normalise_datetime(start)
    cursor = current
    schedule: list[dict[str, object]] = []
    cumulative = 0.0
    risk_score = 0.0

    for milestone in parsed:
        milestone_start = cursor
        milestone_end = milestone_start + timedelta(days=milestone.duration_days)
        buffer_days = max(0.25, milestone.duration_days * (1 - milestone.confidence))
        buffer_end = milestone_end + timedelta(days=buffer_days)
        risk_score += (1 - milestone.confidence) * milestone.duration_days
        cumulative += milestone.duration_days + buffer_days
        cursor = buffer_end
        schedule.append(
            {
                "name": milestone.name,
                "start": _format_iso(milestone_start),
                "end": _format_iso(milestone_end),
                "buffer_end": _format_iso(buffer_end),
                "duration_days": round(milestone.duration_days, 2),
                "confidence": round(milestone.confidence, 2),
                "buffer_days": round(buffer_days, 2),
            }
        )

    risk_class = "low" if risk_score < 3 else "medium" if risk_score < 7 else "high"

    return {
        "start": _format_iso(current),
        "end": schedule[-1]["buffer_end"],
        "total_days": round(cumulative, 2),
        "timeline": schedule,
        "risk": {"score": round(risk_score, 2), "classification": risk_class},
    }


def evaluate_strategy_matrix(
    options: Sequence[Mapping[str, object]] | Sequence[StrategyOption],
    criteria_weights: Mapping[str, float],
) -> dict[str, object]:
    """Rank strategy options using weighted criteria contributions."""

    if not options:
        raise ValueError("at least one strategy option is required")
    if not criteria_weights:
        raise ValueError("at least one criterion weight is required")

    parsed_options = [
        option if isinstance(option, StrategyOption) else StrategyOption.from_mapping(option)
        for option in options
    ]

    weights: dict[str, float] = {}
    for name, value in criteria_weights.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"criterion '{name}' must be numeric") from exc
        if numeric <= 0:
            raise ValueError("criteria weights must be positive")
        weights[name] = numeric

    total_weight = sum(weights.values())
    normalised_weights = {name: value / total_weight for name, value in weights.items()}

    ranking: list[dict[str, object]] = []
    for option in parsed_options:
        contributions: dict[str, float] = {}
        score = 0.0
        for criterion, weight in normalised_weights.items():
            metric = float(option.metrics.get(criterion, 0.0))
            contribution = metric * weight
            contributions[criterion] = round(contribution, 4)
            score += contribution
        ranking.append(
            {
                "name": option.name,
                "score": round(score, 4),
                "coverage": round(
                    len([c for c in normalised_weights if c in option.metrics])
                    / len(normalised_weights),
                    2,
                ),
                "contributions": contributions,
            }
        )

    ranking.sort(key=lambda entry: entry["score"], reverse=True)
    best_score = ranking[0]["score"]
    for entry in ranking:
        entry["relative_score"] = round(entry["score"] / best_score if best_score else 0.0, 3)

    score_gap = best_score - ranking[1]["score"] if len(ranking) > 1 else 0.0
    return {
        "criteria": normalised_weights,
        "options": ranking,
        "best_option": ranking[0],
        "score_gap": round(score_gap, 4),
    }


def forecast_operational_resilience(
    events: Sequence[Mapping[str, object]] | Sequence[ResilienceEvent],
    *,
    start: datetime | None = None,
    horizon_hours: float = 168.0,
) -> dict[str, object]:
    """Forecast operational resilience over a defined horizon."""

    if not events:
        raise ValueError("at least one resilience event is required")
    if horizon_hours <= 0:
        raise ValueError("horizon_hours must be positive")

    parsed_events = [
        event if isinstance(event, ResilienceEvent) else ResilienceEvent.from_mapping(event)
        for event in events
    ]

    cursor = _normalise_datetime(start)
    timeline: list[dict[str, object]] = []
    expected_hours = 0.0
    stress_load = 0.0

    for event in sorted(parsed_events, key=lambda e: (e.likelihood, e.impact_hours), reverse=True):
        window_start = cursor
        window_end = window_start + timedelta(hours=event.total_hours)
        expected = event.total_hours * event.likelihood
        expected_hours += expected
        stress_load += event.impact_hours * event.likelihood
        timeline.append(
            {
                "name": event.name,
                "criticality": event.criticality,
                "likelihood": round(event.likelihood, 2),
                "window_start": _format_iso(window_start),
                "window_end": _format_iso(window_end),
                "total_hours": round(event.total_hours, 2),
                "expected_hours": round(expected, 2),
            }
        )
        buffer_hours = max(1.0, (1 - event.likelihood) * 6)
        cursor = window_end + timedelta(hours=buffer_hours)

    resilience_score = max(0.0, 1 - (expected_hours / horizon_hours))
    if resilience_score >= 0.75:
        classification = "stable"
    elif resilience_score >= 0.45:
        classification = "watch"
    else:
        classification = "critical"

    alerts = [
        {
            "name": entry["name"],
            "severity": entry["criticality"],
            "eta": entry["window_start"],
            "expected_hours": entry["expected_hours"],
        }
        for entry in timeline
    ]

    return {
        "start": _format_iso(_normalise_datetime(start)),
        "horizon_hours": round(horizon_hours, 2),
        "expected_disruption_hours": round(expected_hours, 2),
        "resilience_score": round(resilience_score, 3),
        "risk": {
            "classification": classification,
            "stress_load": round(stress_load, 2),
        },
        "timeline": timeline,
        "alerts": alerts,
    }


def plan_capacity_allocation(
    team_capacity: Mapping[str, float],
    tasks: Sequence[Mapping[str, object]] | Sequence[WorkItem],
    *,
    cycle_length_days: float = 14.0,
) -> dict[str, object]:
    """Allocate work across teams highlighting load factors and spillover cycles."""

    if not team_capacity:
        raise ValueError("provide at least one team capacity entry")
    parsed_capacity: dict[str, float] = {}
    for team, capacity in team_capacity.items():
        name = str(team).strip()
        if not name:
            raise ValueError("team name cannot be empty")
        numeric_capacity = float(capacity)
        if numeric_capacity <= 0:
            raise ValueError("team capacity must be positive")
        parsed_capacity[name] = numeric_capacity

    if not tasks:
        raise ValueError("provide at least one task to schedule")

    parsed_tasks: list[WorkItem] = []
    for task in tasks:
        if isinstance(task, WorkItem):
            parsed_tasks.append(task)
        else:
            parsed_tasks.append(WorkItem.from_mapping(task))

    teams_state: dict[str, dict[str, object]] = {
        team: {"capacity": capacity, "load": 0.0, "assignments": []}
        for team, capacity in parsed_capacity.items()
    }
    priority_counts = Counter()
    unassigned: list[dict[str, object]] = []

    for task in sorted(parsed_tasks, key=lambda item: (item.priority, -item.effort_hours)):
        priority_counts[task.priority] += 1
        team_state = teams_state.get(task.team)
        if team_state is None:
            unassigned.append(
                {
                    "name": task.name,
                    "team": task.team,
                    "effort": task.effort_hours,
                    "priority": task.priority,
                    "reason": "unknown_team",
                }
            )
            continue
        capacity = team_state["capacity"]  # type: ignore[index]
        if capacity <= 0:
            unassigned.append(
                {
                    "name": task.name,
                    "team": task.team,
                    "effort": task.effort_hours,
                    "priority": task.priority,
                    "reason": "zero_capacity",
                }
            )
            continue
        load_before = float(team_state["load"])  # type: ignore[index]
        cycle = int(load_before // capacity) + 1
        team_state["load"] = load_before + task.effort_hours
        completion_cycle = math.ceil(float(team_state["load"]) / capacity)
        team_state["assignments"].append(
            {
                "name": task.name,
                "effort": round(task.effort_hours, 2),
                "priority": task.priority,
                "cycle": cycle,
                "completion_cycle": completion_cycle,
            }
        )

    total_effort = 0.0
    total_capacity = 0.0
    critical_teams: list[str] = []
    max_cycles = 0
    teams_payload: dict[str, dict[str, object]] = {}
    for team, state in teams_state.items():
        capacity = float(state["capacity"])
        load = float(state["load"])
        assignments = state["assignments"]
        load_factor = load / capacity if capacity else None
        cycles_required = math.ceil(load / capacity) if capacity else None
        total_effort += load
        total_capacity += capacity
        if cycles_required:
            max_cycles = max(max_cycles, cycles_required)
        if load_factor and load_factor > 1:
            critical_teams.append(team)
        teams_payload[team] = {
            "capacity": round(capacity, 2),
            "load": round(load, 2),
            "load_factor": round(load_factor, 3) if load_factor is not None else None,
            "cycles_required": cycles_required,
            "assignments": assignments,
        }

    overall_load_factor = total_effort / total_capacity if total_capacity else None
    summary = {
        "total_tasks": len(parsed_tasks),
        "total_effort": round(total_effort, 2),
        "overall_load_factor": round(overall_load_factor, 3) if overall_load_factor else None,
        "critical_teams": sorted(critical_teams),
        "max_cycles": max_cycles,
        "cycle_length_days": round(cycle_length_days, 2),
        "priority_distribution": {priority: count for priority, count in sorted(priority_counts.items())},
    }

    return {"teams": teams_payload, "unassigned": unassigned, "summary": summary}


def simulate_portfolio_outcomes(
    initiatives: Sequence[Mapping[str, object]] | Sequence[PortfolioInitiative],
    *,
    start: datetime | None = None,
) -> dict[str, object]:
    """Roll up multiple initiative timelines into a portfolio-wide outlook."""

    if not initiatives:
        raise ValueError("provide at least one initiative definition")

    parsed_initiatives: list[PortfolioInitiative] = []
    for initiative in initiatives:
        if isinstance(initiative, PortfolioInitiative):
            parsed_initiatives.append(initiative)
        else:
            parsed_initiatives.append(PortfolioInitiative.from_mapping(initiative))

    base_start = _normalise_datetime(start)
    risk_weights = {"low": 1, "medium": 2, "high": 3}
    initiatives_payload: list[dict[str, object]] = []
    weighted_risk = 0.0
    total_weight = 0.0
    total_weighted_value = 0.0
    total_confidence = 0.0
    total_milestones = 0
    earliest_start: datetime | None = None
    latest_end: datetime | None = None
    critical_path: tuple[str, float] | None = None

    for initiative in parsed_initiatives:
        effective_start = initiative.start or base_start
        timeline = simulate_delivery_timeline(initiative.milestones, start=effective_start)
        initiatives_payload.append(
            {
                "name": initiative.name,
                "weight": round(initiative.weight, 2),
                "value": round(initiative.value, 2),
                **timeline,
            }
        )
        risk_weight = risk_weights.get(timeline["risk"]["classification"], 2)
        weighted_risk += risk_weight * initiative.weight
        total_weight += initiative.weight
        total_weighted_value += initiative.value * initiative.weight
        total_confidence += sum(milestone.confidence for milestone in initiative.milestones)
        total_milestones += len(initiative.milestones)
        start_dt = _parse_iso_timestamp(timeline["start"])
        end_dt = _parse_iso_timestamp(timeline["end"])
        earliest_start = start_dt if earliest_start is None else min(earliest_start, start_dt)
        latest_end = end_dt if latest_end is None else max(latest_end, end_dt)
        duration = timeline["total_days"]
        if critical_path is None or duration > critical_path[1]:
            critical_path = (initiative.name, duration)

    if total_weight == 0:
        raise ValueError("initiative weights must be positive")
    portfolio_risk_index = weighted_risk / total_weight
    if portfolio_risk_index < 1.6:
        risk_class = "balanced"
    elif portfolio_risk_index < 2.4:
        risk_class = "watch"
    else:
        risk_class = "elevated"
    avg_confidence = (
        round(total_confidence / total_milestones, 3) if total_milestones else None
    )

    portfolio_summary = {
        "start": _format_iso(earliest_start or base_start),
        "end": _format_iso(latest_end or base_start),
        "overall_days": round(
            (latest_end - earliest_start).total_seconds() / 86400, 2
        )
        if latest_end and earliest_start
        else 0,
        "risk_index": round(portfolio_risk_index, 2),
        "risk_classification": risk_class,
        "critical_path": critical_path[0] if critical_path else None,
        "weighted_value": round(total_weighted_value, 2),
        "average_confidence": avg_confidence,
    }

    return {"initiatives": initiatives_payload, "portfolio": portfolio_summary}


def generate_innovation_radar(
    nodes: Sequence[InnovationNode] | Sequence[Mapping[str, object]]
) -> dict[str, object]:
    """Synthesize a multi-horizon innovation radar and breakthrough tracker."""

    if not nodes:
        raise ValueError("at least one innovation node is required")

    parsed_nodes = [
        node if isinstance(node, InnovationNode) else InnovationNode.from_mapping(node)
        for node in nodes
    ]
    count = len(parsed_nodes)
    novelty_index = sum(node.novelty for node in parsed_nodes) / count
    adoption_index = sum(node.adoption for node in parsed_nodes) / count
    risk_index = sum(node.risk for node in parsed_nodes) / count
    signal_index = sum(node.signal_strength for node in parsed_nodes) / count
    investment_total = sum(node.investment for node in parsed_nodes)
    orbital_momentum = sum(
        math.sqrt(max(node.novelty * node.adoption, 1e-6))
        * math.log1p(max(node.investment, 0.1))
        * (1 - 0.55 * node.risk)
        for node in parsed_nodes
    ) / count
    pioneer_ratio = sum(
        1
        for node in parsed_nodes
        if node.novelty >= 0.72 and node.signal_strength >= 0.6 and node.risk <= 0.65
    ) / count

    horizon_groups: dict[str, list[InnovationNode]] = {}
    for node in parsed_nodes:
        horizon_groups.setdefault(node.horizon, []).append(node)
    horizon_profile: dict[str, dict[str, float]] = {}
    for horizon, group in horizon_groups.items():
        horizon_profile[horizon] = {
            "count": len(group),
            "avg_signal": sum(item.signal_strength for item in group) / len(group),
            "momentum": sum(
                math.sqrt(max(item.novelty * item.adoption, 1e-6)) * (1 - 0.5 * item.risk)
                for item in group
            )
            / len(group),
            "risk": sum(item.risk for item in group) / len(group),
        }

    signal_matrix: list[dict[str, float | str]] = []
    for node in parsed_nodes:
        momentum = math.sqrt(max(node.novelty * node.adoption, 1e-6)) * (1 - 0.45 * node.risk)
        portfolio_bias = (1 - node.risk) * (0.5 + 0.5 * node.novelty) * node.signal_strength
        signal_matrix.append(
            {
                "name": node.name,
                "horizon": node.horizon,
                "novelty": round(node.novelty, 3),
                "adoption": round(node.adoption, 3),
                "risk": round(node.risk, 3),
                "signal_strength": round(node.signal_strength, 3),
                "momentum": round(momentum, 3),
                "portfolio_bias": round(portfolio_bias, 3),
                "investment": round(node.investment, 2),
            }
        )

    breakthrough_candidates = [
        entry
        for entry in sorted(signal_matrix, key=lambda item: item["momentum"], reverse=True)
        if entry["novelty"] >= 0.7 and entry["signal_strength"] >= 0.65 and entry["risk"] <= 0.6
    ][:5]

    wavefront_projection = [
        {
            "horizon": horizon,
            "activation_window_weeks": 3 * idx + 3,
            "signal_focus": round(profile["avg_signal"], 3),
            "momentum_index": round(profile["momentum"], 3),
        }
        for idx, (horizon, profile) in enumerate(
            sorted(horizon_profile.items(), key=lambda item: item[1]["momentum"], reverse=True)
        )
    ]

    return {
        "node_count": count,
        "novelty_index": novelty_index,
        "adoption_index": adoption_index,
        "risk_index": risk_index,
        "signal_index": signal_index,
        "investment_total": investment_total,
        "orbital_momentum": orbital_momentum,
        "pioneer_ratio": pioneer_ratio,
        "horizon_profile": horizon_profile,
        "signal_matrix": signal_matrix,
        "breakthrough_candidates": breakthrough_candidates,
        "wavefront_projection": wavefront_projection,
    }


def generate_innovation_orbit(
    nodes: Sequence[InnovationNode] | Sequence[Mapping[str, object]],
    *,
    waves: int = 3,
    foresight_window_weeks: int = 18,
) -> dict[str, object]:
    """Build an orbital innovation storyline with foresight waves."""

    if waves < 1:
        raise ValueError("waves must be at least 1")
    if foresight_window_weeks <= 0:
        raise ValueError("foresight window must be positive")
    if not nodes:
        raise ValueError("at least one innovation node is required")

    parsed_nodes = [
        node if isinstance(node, InnovationNode) else InnovationNode.from_mapping(node)
        for node in nodes
    ]

    orbit_scores: list[float] = []
    resonance_field: list[dict[str, object]] = []
    horizon_groups: dict[str, list[InnovationNode]] = {}
    for node in parsed_nodes:
        base = 0.45 * node.novelty + 0.35 * node.adoption + 0.2 * node.signal_strength
        damping = max(0.25, 1 - 0.4 * node.risk)
        capital = math.log1p(max(node.investment, 0.0) + 1.0)
        orbit_score = max(0.0, base * damping * capital)
        stability = (1 - node.risk) * (0.5 + 0.5 * node.adoption)
        expansion = node.novelty * node.signal_strength
        resonance_field.append(
            {
                "name": node.name,
                "horizon": node.horizon,
                "orbit_score": round(orbit_score, 3),
                "stability": round(stability, 3),
                "expansion": round(expansion, 3),
            }
        )
        orbit_scores.append(orbit_score)
        horizon_groups.setdefault(node.horizon, []).append(node)

    field_intensity = sum(orbit_scores) / len(orbit_scores)
    flux_index = pstdev(orbit_scores) if len(orbit_scores) > 1 else 0.0
    flux_alert: str
    if flux_index < 0.25:
        flux_alert = "stable"
    elif flux_index < 0.45:
        flux_alert = "dynamic"
    else:
        flux_alert = "volatile"

    resonance_field.sort(key=lambda entry: entry["orbit_score"], reverse=True)
    max_resonance = resonance_field[: min(7, len(resonance_field))]

    horizon_synergy: dict[str, dict[str, object]] = {}
    for horizon, group in horizon_groups.items():
        volume = len(group)
        avg_stability = sum((1 - item.risk) * (0.5 + 0.5 * item.adoption) for item in group) / volume
        avg_expansion = sum(item.novelty * item.signal_strength for item in group) / volume
        vanguard = max(group, key=lambda item: item.signal_strength * (1 - item.risk))
        horizon_synergy[horizon] = {
            "volume": volume,
            "stability": round(avg_stability, 3),
            "expansion": round(avg_expansion, 3),
            "vanguard": vanguard.name,
        }

    sorted_synergy = sorted(
        horizon_synergy.items(), key=lambda item: item[1]["expansion"], reverse=True
    )
    wave_count = min(waves, len(sorted_synergy))
    activation_stride = max(2, foresight_window_weeks // max(wave_count, 1))
    flux_normalised = min(1.0, flux_index / 2.5)

    orbit_waves: list[dict[str, object]] = []
    for idx, (horizon, profile) in enumerate(sorted_synergy[:wave_count]):
        activation_week = activation_stride * (idx + 1)
        confidence = max(0.35, min(0.95, 0.55 + 0.35 * profile["stability"] - 0.2 * flux_normalised))
        thesis = (
            f"Amplify {horizon} via {profile['vanguard']} to harvest {profile['expansion']:.2f} expansion momentum"
        )
        orbit_waves.append(
            {
                "wave": idx + 1,
                "horizon": horizon,
                "activation_week": activation_week,
                "confidence": round(confidence, 3),
                "thesis": thesis,
            }
        )

    insight_threads: list[str] = []
    if max_resonance:
        prime = max_resonance[0]
        insight_threads.append(
            f"{prime['name']} anchors the frontier with orbit score {prime['orbit_score']:.2f}"
        )
    if len(max_resonance) >= 3:
        blend = max_resonance[:3]
        horizons = {entry["horizon"] for entry in blend}
        insight_threads.append(
            "Triad fusion across " + ", ".join(sorted(h.title() for h in horizons)) + " horizons"
        )
    if flux_alert == "volatile":
        insight_threads.append("Flux volatility suggests targeted hedging on exploration bets")

    return {
        "node_count": len(parsed_nodes),
        "field_intensity": round(field_intensity, 3),
        "flux_index": round(flux_index, 3),
        "flux_alert": flux_alert,
        "foresight_window_weeks": foresight_window_weeks,
        "horizon_synergy": horizon_synergy,
        "resonance_field": max_resonance,
        "orbit_waves": orbit_waves,
        "insight_threads": insight_threads,
    }


def progressive_complexity_suite(
    level: int,
    *,
    numeric_terms: int,
    documents: Iterable[str] | None = None,
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone] | None = None,
    start: datetime | None = None,
) -> dict[str, object]:
    """Run progressively complex analytical stages and synthesise their insights."""

    if level not in {1, 2, 3}:
        raise ValueError("level must be between 1 and 3")
    if numeric_terms < 2:
        raise ValueError("numeric_terms must be at least 2")

    completed_stages: list[str] = []
    stage_payloads: list[dict[str, object]] = []
    insights: list[str] = []

    numbers = generate_numeric_intelligence(numeric_terms)
    completed_stages.append("numbers")
    stage_payloads.append(
        {
            "stage": "numbers",
            "description": "Fibonacci-derived intelligence with derivative and ratio trend.",
            "payload": numbers,
        }
    )
    momentum = numbers["derivatives"][-1] if numbers["derivatives"] else 0
    phi = numbers["golden_ratio_estimate"]
    if phi is None:
        insights.append(
            f"Numeric momentum at stage end is {momentum}; insufficient data for golden ratio estimate."
        )
    else:
        insights.append(
            f"Numeric momentum at stage end is {momentum} with golden ratio estimate {phi:.5f}."
        )
    complexity_index = 1.0 + min(1.0, len(numbers["sequence"]) / 25)

    text_payload: dict[str, object] | None = None
    if level >= 2:
        docs = [doc for doc in (documents or []) if doc.strip()]
        if not docs:
            raise ValueError("documents are required for level 2 and above")
        text_payload = analyze_text_corpus(docs)
        completed_stages.append("text")
        stage_payloads.append(
            {
                "stage": "text",
                "description": "Corpus-level lexical analysis across supplied documents.",
                "payload": text_payload,
            }
        )
        insights.append(
            "Lexical field spans "
            f"{text_payload['vocabulary']} tokens with {text_payload['readability']} readability."
        )
        complexity_index += round(float(text_payload["lexical_density"]), 3)

    timeline_payload: dict[str, object] | None = None
    if level >= 3:
        if not milestones:
            raise ValueError("milestones are required for level 3")
        timeline_payload = simulate_delivery_timeline(milestones, start=start)
        completed_stages.append("timeline")
        stage_payloads.append(
            {
                "stage": "timeline",
                "description": "Confidence-aware delivery simulation with buffers and risk scoring.",
                "payload": timeline_payload,
            }
        )
        risk = timeline_payload["risk"]
        insights.append(
            f"Timeline spans {timeline_payload['total_days']} days with {risk['classification']} risk (score {risk['score']})."
        )
        complexity_index += max(0.5, float(risk["score"]) / 10)

    summary = (
        "Executed levels: " + ", ".join(completed_stages)
        + f"; aggregate complexity index {complexity_index:.3f}"
    )

    return {
        "level": level,
        "completed_stages": completed_stages,
        "stages": stage_payloads,
        "insights": insights,
        "complexity_index": round(complexity_index, 3),
        "summary": summary,
        "text_stage": text_payload,
        "timeline_stage": timeline_payload,
    }


def complexity_evolution_series(
    iterations: int,
    *,
    base_numeric_terms: int,
    documents: Iterable[str] | None = None,
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone] | None = None,
    start: datetime | None = None,
) -> dict[str, object]:
    """Run successive progressive suites, increasing scope and complexity per iteration."""

    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if base_numeric_terms < 2:
        raise ValueError("base_numeric_terms must be at least 2")

    document_pool: list[str] = []
    if documents is not None:
        for entry in documents:
            text = str(entry).strip()
            if text:
                document_pool.append(text)

    milestone_pool: list[TimelineMilestone] = []
    if milestones is not None:
        for milestone in milestones:
            if isinstance(milestone, TimelineMilestone):
                milestone_pool.append(milestone)
            else:
                milestone_pool.append(TimelineMilestone.from_mapping(milestone))

    if iterations >= 2 and not document_pool:
        raise ValueError("documents are required for iterations >= 2")
    if iterations >= 3 and not milestone_pool:
        raise ValueError("milestones are required for iterations >= 3")

    phases: list[dict[str, object]] = []
    insights: list[str] = []
    aggregate_index = 0.0
    last_index = 0.0

    for iteration in range(1, iterations + 1):
        level = min(3, iteration)
        numeric_terms = base_numeric_terms + iteration - 1

        docs_for_iteration: list[str] | None = None
        if level >= 2:
            count = min(len(document_pool), max(1, iteration))
            docs_for_iteration = document_pool[:count]

        milestones_for_iteration: list[TimelineMilestone] | None = None
        if level >= 3:
            scale = 1 + (iteration - 1) * 0.15
            confidence_delta = 0.02 * (iteration - 1)
            milestones_for_iteration = [
                TimelineMilestone(
                    name=item.name,
                    duration_days=round(item.duration_days * scale, 3),
                    confidence=max(0.35, min(0.99, item.confidence - confidence_delta)),
                )
                for item in milestone_pool
            ]

        payload = progressive_complexity_suite(
            level,
            numeric_terms=numeric_terms,
            documents=docs_for_iteration,
            milestones=milestones_for_iteration,
            start=start,
        )

        index = float(payload["complexity_index"])
        aggregate_index += index
        delta = index - last_index
        last_index = index

        insights.extend([f"[phase {iteration}] {text}" for text in payload.get("insights", [])])
        phases.append(
            {
                "iteration": iteration,
                "level": level,
                "numeric_terms": numeric_terms,
                "documents_used": len(docs_for_iteration or []),
                "milestones_used": len(milestones_for_iteration or []),
                "complexity_index": round(index, 3),
                "complexity_delta": round(delta, 3),
                "summary": payload.get("summary"),
                "stages": payload.get("completed_stages"),
                "payload": payload,
            }
        )

    gradient = (
        phases[-1]["complexity_index"] - phases[0]["complexity_index"]
        if len(phases) > 1
        else 0.0
    )
    peak = max((phase["complexity_index"] for phase in phases), default=0.0)
    level_breakdown = Counter(phase["level"] for phase in phases)

    return {
        "iterations": iterations,
        "aggregate_complexity": round(aggregate_index, 3),
        "mean_complexity": round(aggregate_index / iterations, 3),
        "complexity_gradient": round(float(gradient), 3),
        "peak_complexity": round(float(peak), 3),
        "documents_available": len(document_pool),
        "milestones_available": len(milestone_pool),
        "level_distribution": {
            f"level_{level}": count for level, count in sorted(level_breakdown.items())
        },
        "phases": phases,
        "insights": insights,
        "final_summary": phases[-1]["summary"] if phases else "",
    }


def assess_alignment_signals(
    signals: Mapping[str, float],
    *,
    target: float = 0.75,
) -> dict[str, object]:
    """Score alignment signals against a target threshold."""

    if not 0 < target <= 1:
        raise ValueError("target must be between 0 and 1")
    if not signals:
        raise ValueError("at least one signal is required")

    normalised: dict[str, float] = {}
    for name, raw_value in signals.items():
        key = str(name).strip()
        if not key:
            raise ValueError("signal names cannot be empty")
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid score for {name!r}") from exc
        if not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("signal scores must be finite values between 0 and 1")
        normalised[key] = value

    scores = list(normalised.values())
    average = sum(scores) / len(scores)
    variability = pstdev(scores) if len(scores) > 1 else 0.0
    cohesion = max(0.0, 1 - variability)
    gap = target - average
    if average >= target:
        classification = "aligned"
    elif average >= target - 0.1:
        classification = "watch"
    else:
        classification = "realign"

    total_score = sum(scores)
    contributions = [
        {
            "name": name,
            "score": round(score, 3),
            "weight": round(score / total_score, 3) if total_score else 0.0,
        }
        for name, score in sorted(
            normalised.items(), key=lambda entry: entry[1], reverse=True
        )
    ]

    strongest = contributions[0]["name"]
    weakest = contributions[-1]["name"]

    return {
        "target": round(target, 2),
        "average_score": round(average, 3),
        "gap": round(gap, 3),
        "classification": classification,
        "cohesion": round(cohesion, 3),
        "signals": contributions,
        "focus": {"strongest": strongest, "weakest": weakest},
    }


def evaluate_operational_readiness(
    capabilities: Sequence[Mapping[str, object]],
    *,
    horizon_weeks: int = 12,
) -> dict[str, object]:
    """Compute readiness indicators across a set of capabilities."""

    if horizon_weeks <= 0:
        raise ValueError("horizon_weeks must be positive")
    if not capabilities:
        raise ValueError("at least one capability is required")

    parsed: list[dict[str, object]] = []
    scores: list[float] = []
    recommendations: list[str] = []
    for capability in capabilities:
        try:
            name = str(capability["name"]).strip()
            coverage = float(capability.get("coverage", 0))
            automation = float(capability.get("automation", 0))
            runbooks = int(capability.get("runbooks", 0))
            incidents = int(capability.get("incidents", 0))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid capability specification") from exc
        if not name:
            raise ValueError("capability name cannot be empty")
        for value in (coverage, automation):
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError("coverage and automation must be between 0 and 1")
        if runbooks < 0 or incidents < 0:
            raise ValueError("runbooks and incidents must be non-negative")

        runbook_score = min(runbooks / 3, 1)
        incident_penalty = min(incidents / max(horizon_weeks / 4, 1), 2)
        resilience = max(0.0, 1 - incident_penalty / 2)
        composite = round(
            0.4 * coverage + 0.3 * automation + 0.2 * runbook_score + 0.1 * resilience,
            3,
        )
        status = "ready" if composite >= 0.75 else "attention" if composite >= 0.55 else "critical"
        parsed.append(
            {
                "name": name,
                "score": composite,
                "coverage": round(coverage, 2),
                "automation": round(automation, 2),
                "runbooks": runbooks,
                "incidents": incidents,
                "status": status,
            }
        )
        scores.append(composite)
        if status != "ready":
            recommendations.append(
                f"Improve {name} via runbook depth and automation hardening"
            )

    average_score = sum(scores) / len(scores)
    classification = (
        "stable" if average_score >= 0.75 else "elevated" if average_score >= 0.55 else "at-risk"
    )

    return {
        "horizon_weeks": horizon_weeks,
        "readiness_index": round(average_score, 3),
        "classification": classification,
        "capabilities": parsed,
        "recommendations": recommendations[:5],
    }


def forecast_portfolio_throughput(
    initiatives: Sequence[Mapping[str, object]],
    *,
    velocity: float = 8,
    horizon_weeks: int = 12,
) -> dict[str, object]:
    """Create a lightweight throughput forecast for a portfolio of initiatives."""

    if velocity <= 0:
        raise ValueError("velocity must be positive")
    if horizon_weeks <= 0:
        raise ValueError("horizon_weeks must be positive")
    if not initiatives:
        raise ValueError("at least one initiative is required")

    class Initiative:
        def __init__(
            self,
            name: str,
            impact: float,
            effort: float,
            confidence: float,
            dependencies: Sequence[str],
        ) -> None:
            self.name = name
            self.impact = impact
            self.effort = effort
            self.confidence = confidence
            self.dependencies = [dep for dep in dependencies if dep]
            value_density = impact / max(effort, 1)
            self.priority = value_density * confidence
            self.remaining_effort = effort

    registry: dict[str, Initiative] = {}
    for entry in initiatives:
        try:
            name = str(entry["name"]).strip()
            impact = float(entry.get("impact", 0))
            effort = float(entry.get("effort", 0))
            confidence = float(entry.get("confidence", 0.7))
            dependencies = entry.get("dependencies", [])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid initiative specification") from exc
        if not name:
            raise ValueError("initiative name cannot be empty")
        if any(not isfinite(value) or value <= 0 for value in (impact, effort)):
            raise ValueError("impact and effort must be positive numbers")
        if not isfinite(confidence) or not 0 < confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if isinstance(dependencies, str):
            dependencies = [
                dep.strip() for dep in dependencies.split(",") if dep.strip()
            ]
        elif not isinstance(dependencies, Sequence):
            raise ValueError("dependencies must be a sequence")
        registry[name] = Initiative(name, impact, effort, confidence, dependencies)

    ordered: list[Initiative] = []
    resolved: set[str] = set()
    pending = dict(registry)
    while pending:
        ready = [
            initiative
            for initiative in pending.values()
            if all(dep in resolved or dep not in registry for dep in initiative.dependencies)
        ]
        if not ready:
            raise ValueError("cyclic or missing dependencies detected")
        ready.sort(key=lambda item: (item.priority, item.confidence), reverse=True)
        for initiative in ready:
            ordered.append(initiative)
            resolved.add(initiative.name)
            pending.pop(initiative.name)

    schedule: list[dict[str, object]] = []
    backlog = ordered.copy()
    sprint = 1
    week_cursor = 0
    while backlog and week_cursor < horizon_weeks:
        capacity = velocity
        assigned: list[dict[str, object]] = []
        while backlog and capacity > 0:
            initiative = backlog[0]
            load = min(initiative.remaining_effort, capacity)
            initiative.remaining_effort -= load
            capacity -= load
            assigned.append(
                {
                    "name": initiative.name,
                    "allocated_effort": round(load, 2),
                    "confidence": round(initiative.confidence, 2),
                }
            )
            if initiative.remaining_effort <= 0:
                backlog.pop(0)
        if not assigned:
            break
        schedule.append(
            {
                "sprint": sprint,
                "start_week": week_cursor,
                "end_week": min(week_cursor + 1, horizon_weeks),
                "load": round(1 - capacity / velocity, 2),
                "initiatives": assigned,
            }
        )
        sprint += 1
        week_cursor += 1

    total_impact = sum(item.impact for item in ordered)
    weighted_confidence = (
        sum(item.confidence * item.impact for item in ordered) / total_impact
        if total_impact
        else 0
    )

    return {
        "throughput_capacity": velocity,
        "horizon_weeks": horizon_weeks,
        "priority_order": [
            {
                "name": item.name,
                "priority": round(item.priority, 3),
                "dependencies": item.dependencies,
            }
            for item in ordered
        ],
        "portfolio_value": round(total_impact, 2),
        "confidence_projection": round(weighted_confidence, 3),
        "sprint_plan": schedule,
    }


def generate_signal_snapshot(signals: Mapping[str, float]) -> dict[str, object]:
    """Create a lightweight signal summary with variance and focus insights."""

    if not isinstance(signals, Mapping) or not signals:
        raise ValueError("signals must be a non-empty mapping")

    ordered: list[tuple[str, float]] = []
    for raw_name, raw_value in signals.items():
        name = str(raw_name).strip()
        if not name:
            raise ValueError("signal names must be non-empty strings")
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"signal '{name}' must be numeric") from exc
        if not isfinite(value):
            raise ValueError(f"signal '{name}' must be finite")
        ordered.append((name, value))

    values = [value for _, value in ordered]
    average = sum(values) / len(values)
    deviation = pstdev(values) if len(values) > 1 else 0.0
    strongest = max(ordered, key=lambda entry: entry[1])
    weakest = min(ordered, key=lambda entry: entry[1])
    momentum = (ordered[-1][1] - ordered[0][1]) if len(ordered) > 1 else 0.0
    spread_ratio = (strongest[1] - weakest[1]) / strongest[1] if strongest[1] else 0.0

    if average >= 0.8:
        classification = "strong"
    elif average >= 0.55:
        classification = "balanced"
    else:
        classification = "weak"

    if momentum > 0.1:
        trend = "accelerating"
    elif momentum < -0.1:
        trend = "declining"
    else:
        trend = "stable"

    enriched = [
        {
            "name": name,
            "value": round(value, 3),
            "deviation": round(value - average, 3),
            "relative_strength": round(value / strongest[1], 3) if strongest[1] else 0.0,
        }
        for name, value in ordered
    ]

    return {
        "signals": enriched,
        "stats": {
            "average": round(average, 3),
            "stdev": round(deviation, 3),
            "spread_ratio": round(spread_ratio, 3),
            "classification": classification,
            "trend": trend,
            "momentum": round(momentum, 3),
            "strongest": strongest[0],
            "weakest": weakest[0],
        },
    }


def build_complexity_checkpoint(
    numeric_terms: int,
    *,
    notes: Iterable[str] | None = None,
    reference: str | None = None,
) -> dict[str, object]:
    """Create the entry-level progressive feature payload.

    The checkpoint folds Fibonacci intelligence with optional context notes and
    returns a concise summary describing the current numeric momentum.  It is
    intentionally lightweight and meant to act as the "base" feature in the
    cascading progression.
    """

    if numeric_terms < 2:
        raise ValueError("numeric_terms must be at least 2")

    annotations = [str(note).strip() for note in (notes or []) if str(note).strip()]
    note_text = annotations[0] if annotations else None
    payload = generate_numeric_intelligence(numeric_terms)
    derivatives = payload.get("derivatives", [])
    ratios = payload.get("ratio_trend", [])
    last_value = payload["sequence"][-1]
    momentum = float(derivatives[-1]) if derivatives else 0.0
    phi = payload.get("golden_ratio_estimate")
    volatility = pstdev(ratios) if len(ratios) > 1 else 0.0
    relative_momentum = momentum / last_value if last_value else 0.0
    if momentum < 0:
        classification = "correcting"
    elif relative_momentum >= 0.5:
        classification = "surging"
    elif relative_momentum >= 0.25:
        classification = "growing"
    elif relative_momentum >= 0.05:
        classification = "steady"
    else:
        classification = "baseline"
    summary = (
        f"Momentum {momentum:.2f} ({classification})"
        + (f", φ≈{phi:.5f}" if phi else "")
    )
    if note_text:
        summary += f" — {note_text}"
    return {
        "reference": reference or f"checkpoint-{numeric_terms}",
        "terms": numeric_terms,
        "payload": payload,
        "momentum": round(momentum, 3),
        "ratio_estimate": round(phi, 5) if phi is not None else None,
        "volatility": round(volatility, 4),
        "classification": classification,
        "note": note_text,
        "summary": summary,
    }


def compose_complexity_journey(
    phases: int,
    *,
    base_numeric_terms: int,
    documents: Iterable[str] | None = None,
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone] | None = None,
    start: datetime | None = None,
    anchor_notes: Iterable[str] | None = None,
) -> dict[str, object]:
    """Create a ladder of progressively complex features.

    Each phase adds additional analysis layers once the required inputs are
    supplied: phase 1 runs the numeric checkpoint, phase 2 adds text analytics,
    and phase 3+ introduces delivery simulations.  Later phases automatically
    scale milestone durations and reduce confidence to mimic higher uncertainty.
    """

    if phases < 1:
        raise ValueError("phases must be at least 1")
    if base_numeric_terms < 2:
        raise ValueError("base_numeric_terms must be at least 2")

    doc_pool = [str(doc).strip() for doc in (documents or []) if str(doc).strip()]
    milestone_pool: list[TimelineMilestone] = []
    if milestones is not None:
        for entry in milestones:
            if isinstance(entry, TimelineMilestone):
                milestone_pool.append(entry)
            elif isinstance(entry, Mapping):
                milestone_pool.append(TimelineMilestone.from_mapping(entry))
            else:  # pragma: no cover - defensive
                raise ValueError("milestones must contain mappings or TimelineMilestone objects")
    note_pool = [str(note).strip() for note in (anchor_notes or []) if str(note).strip()]
    start_anchor = _ensure_datetime(start, None) if start is not None else None

    stages: list[dict[str, object]] = []
    complexity_score = 0.0
    documents_used = 0
    milestones_used = 0
    insights: list[str] = []

    for phase in range(1, phases + 1):
        terms = base_numeric_terms + phase - 1
        note = note_pool[(phase - 1) % len(note_pool)] if note_pool else None
        checkpoint = build_complexity_checkpoint(
            terms,
            notes=[note] if note else None,
            reference=f"phase-{phase}",
        )
        stage_entry: dict[str, object] = {
            "phase": phase,
            "terms": terms,
            "level": 1,
            "checkpoint": checkpoint,
        }
        stage_complexity = 1.0 + math.log(max(terms, 2), 2)
        text_payload: dict[str, object] | None = None
        if phase >= 2 and doc_pool:
            doc_count = min(len(doc_pool), max(1, phase))
            documents_used += doc_count
            text_payload = analyze_text_corpus(doc_pool[:doc_count])
            stage_entry["text"] = text_payload
            stage_entry["level"] = max(stage_entry["level"], 2)
            stage_complexity += float(text_payload["lexical_density"])
        elif phase >= 2:
            insights.append(f"Phase {phase}: text stage skipped (no documents provided)")

        timeline_payload: dict[str, object] | None = None
        if phase >= 3 and milestone_pool:
            scale = 1 + 0.12 * (phase - 1)
            confidence_delta = 0.03 * (phase - 2)
            adjusted = [
                TimelineMilestone(
                    name=item.name,
                    duration_days=round(item.duration_days * scale, 3),
                    confidence=max(0.35, min(0.99, item.confidence - confidence_delta)),
                )
                for item in milestone_pool
            ]
            milestones_used += len(adjusted)
            stage_start = (
                start_anchor + timedelta(days=(phase - 1) * 2)
                if start_anchor is not None
                else None
            )
            timeline_payload = simulate_delivery_timeline(adjusted, start=stage_start)
            stage_entry["timeline"] = timeline_payload
            stage_entry["level"] = max(stage_entry["level"], 3)
            risk_score = float(timeline_payload["risk"]["score"])
            stage_complexity += max(0.5, risk_score / 5)
        elif phase >= 3:
            insights.append(f"Phase {phase}: timeline stage skipped (no milestones provided)")

        stage_entry["complexity"] = round(stage_complexity, 3)
        stages.append(stage_entry)
        complexity_score += stage_complexity
        insights.append(
            f"Phase {phase}: {checkpoint['summary']} (level {stage_entry['level']})"
        )
        if text_payload:
            insights.append(
                f"Phase {phase}: text readability {text_payload['readability']} across "
                f"{text_payload['documents']} documents"
            )
        if timeline_payload:
            risk = timeline_payload["risk"]
            insights.append(
                f"Phase {phase}: timeline risk {risk['classification']} (score {risk['score']})"
            )

    summary_parts = [
        f"{phases} phase(s)",
        f"documents used {documents_used}",
        f"milestones used {milestones_used}",
    ]
    summary = ", ".join(summary_parts)
    return {
        "phase_count": phases,
        "base_terms": base_numeric_terms,
        "documents_available": len(doc_pool),
        "milestones_available": len(milestone_pool),
        "notes_available": len(note_pool),
        "documents_analyzed": documents_used,
        "milestones_applied": milestones_used,
        "complexity_index": round(complexity_score, 3),
        "phases": stages,
        "insights": insights,
        "summary": summary,
        "start_reference": _format_iso(start_anchor) if start_anchor else None,
    }


def orchestrate_complexity_summit(agenda: Mapping[str, object]) -> dict[str, object]:
    """Fuse multiple progressive features into an apex "summit" insight."""

    if not isinstance(agenda, Mapping) or not agenda:
        raise ValueError("agenda must be a non-empty mapping")

    try:
        phases = int(agenda.get("phases", 3))
        base_terms = int(agenda.get("base_numeric_terms", 8))
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError("phases and base_numeric_terms must be numeric") from exc

    notes = agenda.get("notes")
    note_values = [str(note).strip() for note in (notes or []) if str(note).strip()] if notes else None
    documents = agenda.get("documents")
    doc_values = None
    if documents is not None:
        doc_values = [str(doc).strip() for doc in documents if str(doc).strip()]
        if not doc_values:
            raise ValueError("documents must include at least one non-empty entry")
    milestones = agenda.get("milestones")
    milestone_sequence = None
    if milestones is not None:
        if not isinstance(milestones, Sequence):  # pragma: no cover - defensive
            raise ValueError("milestones must be a sequence")
        milestone_sequence = list(milestones)
        if not milestone_sequence:
            milestone_sequence = None
    start_value = agenda.get("start")
    start_dt = _ensure_datetime(start_value, None) if start_value is not None else None

    journey = compose_complexity_journey(
        phases,
        base_numeric_terms=base_terms,
        documents=doc_values,
        milestones=milestone_sequence,
        start=start_dt,
        anchor_notes=note_values,
    )

    supplemental: dict[str, object] = {}
    insights = list(journey.get("insights", []))
    total_score = float(journey.get("complexity_index", 0.0))

    raw_signals = agenda.get("signals")
    signals_payload: dict[str, float] | None = None
    if raw_signals is not None:
        if not isinstance(raw_signals, Mapping) or not raw_signals:
            raise ValueError("signals must be a non-empty mapping")
        signals_payload = {}
        for key, value in raw_signals.items():
            name = str(key).strip()
            if not name:
                raise ValueError("signal names cannot be empty")
            try:
                signals_payload[name] = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"signal '{key}' must be numeric") from exc
        if not signals_payload:
            raise ValueError("signals must include at least one numeric entry")

    alignment_target = float(agenda.get("alignment_target", 0.75))
    if signals_payload:
        snapshot = generate_signal_snapshot(signals_payload)
        supplemental["signals"] = snapshot
        total_score += snapshot["stats"]["average"] * 2
        insights.append(
            f"Signals trending {snapshot['stats']['trend']} "
            f"({snapshot['stats']['classification']} strength)"
        )
        alignment_payload = assess_alignment_signals(signals_payload, target=alignment_target)
        supplemental["alignment"] = alignment_payload
        total_score += max(0.0, 1 - abs(float(alignment_payload["gap"])))
        insights.append(
            f"Alignment gap {alignment_payload['gap']} ({alignment_payload['classification']})"
        )

    strategy_payload: dict[str, object] | None = None
    raw_strategy = agenda.get("strategy")
    if raw_strategy is not None:
        if not isinstance(raw_strategy, Mapping):
            raise ValueError("strategy must be a mapping with options and criteria")
        options = raw_strategy.get("options")
        criteria = raw_strategy.get("criteria")
        if options is None or criteria is None:
            raise ValueError("strategy requires 'options' and 'criteria'")
        strategy_payload = evaluate_strategy_matrix(options, criteria)
        supplemental["strategy"] = strategy_payload
        best_option = strategy_payload["best_option"]
        total_score += float(best_option["score"])
        insights.append(
            f"Strategy favours {best_option['name']} (score {best_option['score']})"
        )

    if total_score >= 16:
        grade = "apex"
    elif total_score >= 11:
        grade = "expedition"
    elif total_score >= 7:
        grade = "expansion"
    else:
        grade = "foundation"

    summary = (
        f"Summit executed {journey['phase_count']} phase(s) with {len(supplemental)} "
        "supplemental module(s)."
    )
    return {
        "phases": phases,
        "score": round(total_score, 3),
        "grade": grade,
        "journey": journey,
        "supplemental": supplemental,
        "insights": insights,
        "summary": summary,
    }


def orchestrate_complexity_constellation(program: Mapping[str, object]) -> dict[str, object]:
    """Execute multiple summit agendas and synthesise constellation-level insights."""

    if not isinstance(program, Mapping):
        raise ValueError("program must be a mapping containing scenarios")

    scenarios = program.get("scenarios")
    if not isinstance(scenarios, Sequence) or not scenarios:
        raise ValueError("program requires a non-empty 'scenarios' sequence")

    defaults = program.get("defaults") or {}
    if defaults and not isinstance(defaults, Mapping):
        raise ValueError("program 'defaults' must be a mapping")

    grade_weights = {"foundation": 1, "expansion": 2, "expedition": 3, "apex": 4}
    grade_counts: Counter[str] = Counter()
    scenario_results: list[dict[str, object]] = []
    score_series: list[float] = []
    insight_pool: list[str] = []
    tag_distribution: Counter[str] = Counter()
    best_entry: dict[str, object] | None = None
    worst_entry: dict[str, object] | None = None
    best_score = -math.inf
    worst_score = math.inf

    for index, raw_scenario in enumerate(scenarios, 1):
        if not isinstance(raw_scenario, Mapping):
            raise ValueError(f"scenario at position {index} must be a mapping")
        name = str(raw_scenario.get("name", "")).strip() or f"scenario-{index}"
        agenda = dict(defaults)
        for key, value in raw_scenario.items():
            if key in {"name", "tags"}:
                continue
            agenda[key] = value
        if not agenda:
            raise ValueError(f"scenario '{name}' did not define an agenda")
        try:
            summit_payload = orchestrate_complexity_summit(agenda)
        except ValueError as exc:
            raise ValueError(f"scenario '{name}' invalid: {exc}") from exc

        grade = str(summit_payload["grade"])
        score = float(summit_payload["score"])
        grade_counts[grade] += 1
        score_series.append(score)
        journey = summit_payload.get("journey", {})
        scenario_entry: dict[str, object] = {
            "name": name,
            "grade": grade,
            "score": round(score, 3),
            "summary": summit_payload.get("summary"),
            "complexity_index": journey.get("complexity_index"),
            "phases": journey.get("phase_count"),
            "insights": summit_payload.get("insights", [])[:4],
        }
        raw_tags = raw_scenario.get("tags")
        if isinstance(raw_tags, Sequence) and not isinstance(raw_tags, (str, bytes)):
            tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
            if tags:
                scenario_entry["tags"] = tags
                tag_distribution.update(tags)
        scenario_results.append(scenario_entry)

        if score > best_score:
            best_score = score
            best_entry = scenario_entry
        if score < worst_score:
            worst_score = score
            worst_entry = scenario_entry

        for insight in summit_payload.get("insights", [])[:3]:
            insight_pool.append(f"[{name}] {insight}")

    total = len(scenario_results)
    average_score = sum(score_series) / total
    peak_score = max(score_series)
    floor_score = min(score_series)
    score_range = peak_score - floor_score if total > 1 else 0.0
    stability_index = 1.0
    if peak_score > 0 and score_range > 0:
        stability_index = max(0.0, 1 - (score_range / peak_score))

    grade_vector = 0.0
    if grade_counts:
        weighted = sum(grade_weights.get(grade, 1) * count for grade, count in grade_counts.items())
        grade_vector = weighted / sum(grade_counts.values())

    if average_score >= 15 and grade_vector >= 3.5:
        constellation_grade = "stellar"
    elif average_score >= 11 and grade_vector >= 2.5:
        constellation_grade = "orbital"
    elif average_score >= 8 and grade_vector >= 1.8:
        constellation_grade = "ascending"
    else:
        constellation_grade = "formative"

    progression: list[dict[str, object]] = []
    if len(scenario_results) > 1:
        for previous, current in zip(scenario_results, scenario_results[1:]):
            prev_grade = previous["grade"]
            curr_grade = current["grade"]
            grade_shift = grade_weights.get(curr_grade, 1) - grade_weights.get(prev_grade, 1)
            progression.append(
                {
                    "from": previous["name"],
                    "to": current["name"],
                    "score_delta": round(float(current["score"]) - float(previous["score"]), 3),
                    "grade_shift": grade_shift,
                }
            )

    if best_entry:
        best_entry = dict(best_entry)
    if worst_entry:
        worst_entry = dict(worst_entry)

    summary = (
        f"Constellation spanning {total} scenario(s) with average score {average_score:.2f} "
        f"({constellation_grade})."
    )

    insights = [
        f"Average score {average_score:.2f} with range {score_range:.2f}",
        f"Grade vector {grade_vector:.2f} ({constellation_grade})",
    ]
    if tag_distribution:
        top_tag, tag_count = tag_distribution.most_common(1)[0]
        insights.append(f"Dominant focus tag '{top_tag}' appears {tag_count} time(s)")
    insights.extend(insight_pool[:8])

    return {
        "scenario_count": total,
        "average_score": round(average_score, 3),
        "score_range": round(score_range, 3),
        "stability_index": round(stability_index, 3),
        "grade_distribution": dict(grade_counts),
        "grade_vector": round(grade_vector, 3),
        "constellation_grade": constellation_grade,
        "best_scenario": best_entry,
        "worst_scenario": worst_entry,
        "scenarios": scenario_results,
        "progression": progression,
        "insights": insights,
        "summary": summary,
    }


def synthesize_operational_dashboard(
    *,
    signals: Mapping[str, float],
    documents: Iterable[str],
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone],
    start: datetime | None = None,
) -> dict[str, object]:
    """Fuse signal, textual, and delivery insights into a single dashboard."""

    snapshot = generate_signal_snapshot(signals)
    text_payload = analyze_text_corpus(documents)
    timeline_payload = simulate_delivery_timeline(milestones, start=start)

    signal_strength = snapshot["stats"]["classification"]
    readability = text_payload["readability"]
    risk = timeline_payload["risk"]["classification"]

    blend_score = 0.0
    blend_score += {"weak": 0.3, "balanced": 0.6, "strong": 0.9}[signal_strength]
    blend_score += {"complex": 0.4, "balanced": 0.7, "concise": 0.9}[readability]
    blend_score += {"high": 0.3, "medium": 0.6, "low": 0.9}[risk]
    blend_score /= 3

    if blend_score >= 0.8:
        outlook = "confident"
    elif blend_score >= 0.55:
        outlook = "watch"
    else:
        outlook = "intervene"

    highlights = [
        f"Signals trending {snapshot['stats']['trend']} with {signal_strength} strength.",
        f"Text corpus {readability} readability over {text_payload['documents']} documents.",
        (
            "Timeline spans "
            f"{timeline_payload['total_days']} days ({risk} risk, buffers applied)."
        ),
    ]

    return {
        "snapshot": snapshot,
        "text": text_payload,
        "timeline": timeline_payload,
        "outlook": outlook,
        "composite_score": round(blend_score, 3),
        "highlights": highlights,
    }


def orchestrate_complexity_progression(plan: Mapping[str, object]) -> dict[str, object]:
    """Execute increasingly complex feature sets defined within ``plan``."""

    if not isinstance(plan, Mapping) or not plan:
        raise ValueError("plan must be a non-empty mapping")

    results: dict[str, dict[str, object]] = {}
    executed: list[str] = []
    markers: list[dict[str, object]] = []
    insights: list[str] = []
    total_complexity = 0.0

    base_start: datetime | None = None
    if plan.get("start") is not None:
        base_start = _ensure_datetime(plan["start"], None)

    def _collect_documents(value: object | None) -> list[str] | None:
        if value is None:
            return None
        return _coerce_string_sequence(value, "documents")

    def _collect_milestones(value: object | None) -> list[Mapping[str, object]] | None:
        if value is None:
            return None
        return _coerce_sequence_of_mappings(value, "milestones")

    suite_config = plan.get("progressive_suite")
    if suite_config:
        if not isinstance(suite_config, Mapping):
            raise ValueError("progressive_suite must be a mapping")
        docs = _collect_documents(suite_config.get("documents"))
        milestones = _collect_milestones(suite_config.get("milestones"))
        start_value = suite_config.get("start")
        start_dt = _ensure_datetime(start_value, base_start) if start_value or base_start else None
        payload = progressive_complexity_suite(
            int(suite_config.get("level", 2)),
            numeric_terms=int(suite_config.get("numeric_terms", 8)),
            documents=docs,
            milestones=milestones,
            start=start_dt,
        )
        results["progressive_suite"] = payload
        executed.append("progressive_suite")
        total_complexity += float(payload.get("complexity_index", 0.0))
        markers.append(
            {
                "name": "progressive_suite",
                "complexity": payload.get("complexity_index"),
                "detail": payload.get("summary"),
            }
        )
        insights.extend([f"[suite] {text}" for text in payload.get("insights", [])])

    series_config = plan.get("evolution_series")
    if series_config:
        if not isinstance(series_config, Mapping):
            raise ValueError("evolution_series must be a mapping")
        docs = _collect_documents(series_config.get("documents"))
        milestones = _collect_milestones(series_config.get("milestones"))
        start_value = series_config.get("start")
        start_dt = _ensure_datetime(start_value, base_start) if start_value or base_start else None
        payload = complexity_evolution_series(
            int(series_config.get("iterations", 2)),
            base_numeric_terms=int(series_config.get("base_numeric_terms", 6)),
            documents=docs,
            milestones=milestones,
            start=start_dt,
        )
        results["evolution_series"] = payload
        executed.append("evolution_series")
        total_complexity += float(payload.get("aggregate_complexity", 0.0))
        markers.append(
            {
                "name": "evolution_series",
                "complexity": payload.get("aggregate_complexity"),
                "detail": payload.get("final_summary"),
            }
        )
        insights.extend([f"[series] {text}" for text in payload.get("insights", [])])

    cascade_config = plan.get("cascade")
    if cascade_config:
        if not isinstance(cascade_config, Mapping):
            raise ValueError("cascade must be a mapping")
        stages = cascade_config.get("stages")
        start_value = cascade_config.get("start")
        if not stages:
            raise ValueError("cascade requires stages")
        payload = execute_complexity_cascade(
            stages,
            default_start=_ensure_datetime(start_value, base_start)
            if start_value or base_start
            else None,
        )
        results["cascade"] = payload
        executed.append("cascade")
        total_complexity += float(payload.get("complexity_score", 0.0))
        markers.append(
            {
                "name": "cascade",
                "complexity": payload.get("complexity_score"),
                "detail": ", ".join(payload.get("insights", [])[:3]),
            }
        )
        insights.extend([f"[cascade] {text}" for text in payload.get("insights", [])])

    if not results:
        raise ValueError("plan did not include any executable sections")

    complexity_values = [
        float(marker.get("complexity", 0.0))
        for marker in markers
        if marker.get("complexity")
    ]
    escalation = 0.0
    if len(complexity_values) > 1 and min(complexity_values) > 0:
        escalation = max(complexity_values) / min(complexity_values)

    profile = {
        "total_complexity": round(total_complexity, 3),
        "steps": markers,
        "executed": executed,
        "escalation_factor": round(escalation, 3) if escalation else 0.0,
    }

    return {
        "results": results,
        "execution_order": executed,
        "complexity_profile": profile,
        "insights": insights,
    }


_CASCADE_COMPLEXITY_WEIGHTS = {
    "numbers": 1.0,
    "alignment": 1.1,
    "text": 1.2,
    "strategy": 1.4,
    "capacity": 1.5,
    "timeline": 1.6,
    "readiness": 1.7,
    "resilience": 1.8,
    "portfolio": 1.9,
    "throughput": 2.0,
}


def execute_complexity_cascade(
    stages: Sequence[Mapping[str, object]] | Sequence[CascadeStage],
    *,
    default_start: datetime | None = None,
) -> dict[str, object]:
    """Execute progressively complex analytical stages defined in ``stages``.

    Each stage dictionary must contain a ``type`` field referencing one of the
    supported progressive helpers (numbers, text, timeline, strategy, capacity,
    alignment, readiness, resilience, portfolio, or throughput). Parameters for
    the underlying helper should be provided via the ``params`` mapping.
    """

    if not stages:
        raise ValueError("provide at least one cascade stage")

    parsed: list[CascadeStage] = [
        stage if isinstance(stage, CascadeStage) else CascadeStage.from_mapping(stage)
        for stage in stages
    ]

    start_anchor = _normalise_datetime(default_start)
    stage_results: list[dict[str, object]] = []
    insights: list[str] = []
    distribution: Counter[str] = Counter()
    complexity_score = 0.0
    previous_payload: dict[str, object] | None = None

    for index, stage in enumerate(parsed, 1):
        payload = _run_cascade_stage(stage, default_start=start_anchor)
        entry: dict[str, object] = {
            "name": stage.name,
            "type": stage.kind,
            "payload": payload,
        }
        insight = _summarise_stage_insight(
            stage.kind, payload, previous_payload=previous_payload
        )
        if insight:
            entry["insight"] = insight
            insights.append(f"{stage.name}: {insight}")
        stage_results.append(entry)
        distribution[stage.kind] += 1
        complexity_score += _CASCADE_COMPLEXITY_WEIGHTS.get(stage.kind, 1.0) * (
            1 + index / 10
        )
        previous_payload = payload

    return {
        "start_reference": _format_iso(start_anchor),
        "stage_count": len(stage_results),
        "stage_type_distribution": dict(distribution),
        "stages": stage_results,
        "insights": insights,
        "complexity_score": round(complexity_score, 3),
    }


def _run_cascade_stage(
    stage: CascadeStage,
    *,
    default_start: datetime | None,
) -> dict[str, object]:
    params = stage.params
    if stage.kind == "numbers":
        count = int(params.get("count", 8))
        return generate_numeric_intelligence(count)
    if stage.kind == "text":
        documents = _coerce_string_sequence(params.get("documents"), "documents")
        return analyze_text_corpus(documents)
    if stage.kind == "timeline":
        milestones = _coerce_sequence_of_mappings(params.get("milestones"), "milestones")
        start = _ensure_datetime(params.get("start"), default_start)
        return simulate_delivery_timeline(milestones, start=start)
    if stage.kind == "strategy":
        options = _coerce_sequence_of_mappings(params.get("options"), "options")
        criteria = _coerce_float_mapping(params.get("criteria"), "criteria")
        return evaluate_strategy_matrix(options, criteria)
    if stage.kind == "capacity":
        capacity = _coerce_float_mapping(params.get("capacity"), "capacity")
        tasks = _coerce_sequence_of_mappings(params.get("tasks"), "tasks")
        cycle = float(params.get("cycle_length_days", 14.0))
        return plan_capacity_allocation(capacity, tasks, cycle_length_days=cycle)
    if stage.kind == "alignment":
        signals = _coerce_float_mapping(params.get("signals"), "signals")
        target = float(params.get("target", 0.75))
        return assess_alignment_signals(signals, target=target)
    if stage.kind == "readiness":
        capabilities = _coerce_sequence_of_mappings(
            params.get("capabilities"), "capabilities"
        )
        horizon = int(params.get("horizon_weeks", 12))
        return evaluate_operational_readiness(capabilities, horizon_weeks=horizon)
    if stage.kind == "resilience":
        events = _coerce_sequence_of_mappings(params.get("events"), "events")
        horizon = float(params.get("horizon_hours", 168.0))
        start = _ensure_datetime(params.get("start"), default_start)
        return forecast_operational_resilience(events, start=start, horizon_hours=horizon)
    if stage.kind == "portfolio":
        initiatives = _coerce_sequence_of_mappings(
            params.get("initiatives"), "initiatives"
        )
        start = _ensure_datetime(params.get("start"), default_start)
        return simulate_portfolio_outcomes(initiatives, start=start)
    if stage.kind == "throughput":
        initiatives = _coerce_sequence_of_mappings(
            params.get("initiatives"), "initiatives"
        )
        velocity = float(params.get("velocity", 8))
        horizon_weeks = int(params.get("horizon_weeks", 12))
        return forecast_portfolio_throughput(
            initiatives, velocity=velocity, horizon_weeks=horizon_weeks
        )
    raise ValueError(f"unsupported cascade stage type '{stage.kind}'")


def _summarise_stage_insight(
    stage_type: str,
    payload: Mapping[str, object],
    *,
    previous_payload: Mapping[str, object] | None,
) -> str | None:
    if stage_type == "numbers":
        sequence = payload.get("sequence", [])
        if sequence:
            return f"sequence peaked at {sequence[-1]}"
    elif stage_type == "text":
        readability = payload.get("readability")
        vocab = payload.get("vocabulary")
        if readability and vocab is not None:
            return f"readability {readability} across {vocab} terms"
    elif stage_type == "timeline":
        risk = payload.get("risk", {})
        classification = risk.get("classification")
        total_days = payload.get("total_days")
        if classification:
            return f"timeline spans {total_days} days ({classification} risk)"
    elif stage_type == "strategy":
        best = payload.get("best_option", {})
        if best:
            return f"best option {best.get('name')} scored {best.get('score')}"
    elif stage_type == "capacity":
        summary = payload.get("summary", {})
        overloaded = len(summary.get("critical_teams", []) or [])
        return f"capacity plan flagged {overloaded} overloaded team(s)"
    elif stage_type == "alignment":
        return f"alignment {payload.get('classification')} with gap {payload.get('gap')}"
    elif stage_type == "readiness":
        return f"readiness index {payload.get('readiness_index')} ({payload.get('classification')})"
    elif stage_type == "resilience":
        risk = payload.get("risk", {})
        return f"resilience score {payload.get('resilience_score')} ({risk.get('classification')})"
    elif stage_type == "portfolio":
        portfolio = payload.get("portfolio", {})
        return f"portfolio value {portfolio.get('weighted_value')} ({portfolio.get('risk_classification')})"
    elif stage_type == "throughput":
        return (
            f"throughput horizon {payload.get('horizon_weeks')}w with confidence "
            f"{payload.get('confidence_projection')}"
        )
    if previous_payload and stage_type == "timeline":  # pragma: no cover - defensive
        return "timeline contextualised against previous stage"
    return None


def execute_feature_escalation(
    signals: Mapping[str, float],
    *,
    capabilities: Sequence[Mapping[str, object]] | None = None,
    events: Sequence[Mapping[str, object]]
    | Sequence[ResilienceEvent]
    | None = None,
    initiatives: Sequence[Mapping[str, object]]
    | Sequence[PortfolioInitiative]
    | None = None,
    target: float = 0.75,
    readiness_horizon_weeks: int = 12,
    resilience_horizon_hours: float = 168.0,
    throughput_velocity: float = 8.0,
    throughput_horizon_weeks: int = 12,
    start: datetime | None = None,
) -> dict[str, object]:
    """Run a curated showcase of increasingly complex features.

    The escalation begins with lightweight alignment scoring and expands through
    readiness, resilience, and portfolio analytics as additional datasets are
    supplied. Each successive stage compounds the complexity score, allowing
    callers to see how insights evolve as more sophisticated features are
    introduced.
    """

    if not signals:
        raise ValueError("at least one alignment signal is required")

    capability_list = list(capabilities or [])
    event_list = list(events or [])
    initiative_list = list(initiatives or [])
    start_anchor = _normalise_datetime(start)

    coverage = {
        "alignment": bool(signals),
        "readiness": bool(capability_list),
        "resilience": bool(event_list),
        "portfolio": bool(initiative_list),
        "throughput": bool(initiative_list),
    }

    stages: list[dict[str, object]] = []
    insights: list[str] = []
    escalation_curve: list[dict[str, object]] = []
    previous_payload: Mapping[str, object] | None = None
    total_complexity = 0.0

    def register_stage(
        stage_type: str,
        label: str,
        payload: Mapping[str, object],
    ) -> None:
        nonlocal previous_payload, total_complexity
        index = len(stages) + 1
        base_weight = _CASCADE_COMPLEXITY_WEIGHTS.get(stage_type, 1.0)
        contribution = base_weight * (1 + index / 10)
        total_complexity += contribution
        entry: dict[str, object] = {
            "label": label,
            "type": stage_type,
            "payload": payload,
            "complexity_contribution": round(contribution, 3),
            "cumulative_complexity": round(total_complexity, 3),
        }
        insight = _summarise_stage_insight(
            stage_type, payload, previous_payload=previous_payload
        )
        if insight:
            entry["insight"] = insight
            insights.append(f"{label}: {insight}")
        stages.append(entry)
        escalation_curve.append(
            {
                "stage": label,
                "cumulative_complexity": entry["cumulative_complexity"],
            }
        )
        previous_payload = payload

    alignment_payload = assess_alignment_signals(signals, target=target)
    register_stage("alignment", "Alignment baseline", alignment_payload)

    if capability_list:
        readiness_payload = evaluate_operational_readiness(
            capability_list, horizon_weeks=readiness_horizon_weeks
        )
        register_stage("readiness", "Capability readiness", readiness_payload)

    if event_list:
        resilience_payload = forecast_operational_resilience(
            event_list,
            start=start_anchor,
            horizon_hours=resilience_horizon_hours,
        )
        register_stage("resilience", "Resilience horizon", resilience_payload)

    if initiative_list:
        portfolio_payload = simulate_portfolio_outcomes(
            initiative_list, start=start_anchor
        )
        register_stage("portfolio", "Portfolio synthesis", portfolio_payload)

        throughput_payload = forecast_portfolio_throughput(
            initiative_list,
            velocity=throughput_velocity,
            horizon_weeks=throughput_horizon_weeks,
        )
        register_stage("throughput", "Throughput projection", throughput_payload)

    final_stage = stages[-1]["label"] if stages else None
    return {
        "start_reference": _format_iso(start_anchor),
        "stage_count": len(stages),
        "complexity_score": round(total_complexity, 3),
        "stages": stages,
        "insights": insights,
        "escalation_curve": escalation_curve,
        "coverage": {key: bool(value) for key, value in coverage.items()},
        "final_stage": final_stage,
    }


def construct_complexity_foundation(
    segments: Sequence[object],
    *,
    reference_prefix: str = "segment",
) -> dict[str, object]:
    """Create a baseline layer of checkpoints that other features can build on."""

    if not isinstance(segments, Sequence) or not segments:
        raise ValueError("segments must be a non-empty sequence")

    prefix = reference_prefix.strip() or "segment"
    entries: list[dict[str, object]] = []
    classification_counts: Counter[str] = Counter()
    total_momentum = 0.0
    volatility_values: list[float] = []
    insights: list[str] = []

    for index, raw_segment in enumerate(segments, 1):
        notes: Iterable[str] | None = None
        reference = None
        raw_terms: object | None = None
        if isinstance(raw_segment, Mapping):
            raw_terms = raw_segment.get("terms", raw_segment.get("count"))
            reference = raw_segment.get("reference")
            raw_notes = raw_segment.get("notes")
            if raw_notes is not None:
                if isinstance(raw_notes, str):
                    notes = [raw_notes]
                elif isinstance(raw_notes, Iterable):
                    candidate_notes = [
                        str(note).strip() for note in raw_notes if str(note).strip()
                    ]
                    notes = candidate_notes or None
                else:  # pragma: no cover - defensive
                    raise ValueError("notes must be a string or iterable of strings")
        else:
            raw_terms = raw_segment

        try:
            terms = int(raw_terms)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"segment at position {index} must define numeric 'terms'"
            ) from exc
        if terms < 2:
            raise ValueError("each segment must reference at least two terms")

        checkpoint = build_complexity_checkpoint(
            terms,
            notes=notes,
            reference=reference or f"{prefix}-{index}",
        )
        entry = {
            "reference": checkpoint["reference"],
            "terms": checkpoint["terms"],
            "classification": checkpoint["classification"],
            "momentum": checkpoint["momentum"],
            "volatility": checkpoint["volatility"],
            "summary": checkpoint["summary"],
            "checkpoint": checkpoint,
        }
        entries.append(entry)
        classification_counts[checkpoint["classification"]] += 1
        total_momentum += float(checkpoint["momentum"])
        volatility_values.append(float(checkpoint["volatility"]))
        insights.append(
            f"{entry['reference']}: {entry['classification']} momentum {entry['momentum']}"
        )

    momentum_average = total_momentum / len(entries)
    volatility_range = (
        max(volatility_values) - min(volatility_values)
        if len(volatility_values) > 1
        else volatility_values[0]
        if volatility_values
        else 0.0
    )
    peak_entry = max(entries, key=lambda item: item["momentum"], default=None)
    summary = (
        f"Constructed {len(entries)} foundation segment(s) with average momentum "
        f"{momentum_average:.2f}."
    )
    if peak_entry:
        summary += (
            f" Peak segment {peak_entry['reference']} classified"
            f" {peak_entry['classification']}."
        )

    return {
        "segment_count": len(entries),
        "segments": entries,
        "classification_distribution": dict(classification_counts),
        "momentum_average": round(momentum_average, 3),
        "volatility_range": round(volatility_range, 4),
        "peak_segment": peak_entry["reference"] if peak_entry else None,
        "insights": insights[:6],
        "summary": summary,
    }


def simulate_complexity_orbit(
    orbits: Sequence[object] | Mapping[str, object],
    *,
    documents: Iterable[str] | None = None,
    milestones: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone] | None = None,
    start: datetime | None = None,
) -> dict[str, object]:
    """Cascade progressive suites across multiple checkpoints."""

    if isinstance(orbits, Mapping) and "segments" in orbits:
        orbit_candidates = orbits["segments"]
    else:
        orbit_candidates = orbits

    if not isinstance(orbit_candidates, Sequence) or not orbit_candidates:
        raise ValueError("orbits must be a non-empty sequence")

    doc_pool = _normalise_optional_documents(documents)
    milestone_pool = _normalise_optional_milestones(milestones)
    start_anchor = _normalise_datetime(start)

    results: list[dict[str, object]] = []
    aggregate_complexity = 0.0
    levels: list[int] = []
    insights: list[str] = []
    peak_reference: str | None = None
    peak_complexity = -math.inf

    for position, candidate in enumerate(orbit_candidates, 1):
        if isinstance(candidate, Mapping):
            checkpoint = candidate.get("checkpoint")
            raw_terms = (
                candidate.get("terms")
                or (checkpoint or {}).get("terms")
                or candidate.get("count")
            )
            classification = (
                candidate.get("classification")
                or (checkpoint or {}).get("classification")
            )
            reference = (
                candidate.get("reference") or (checkpoint or {}).get("reference")
            )
            level_override = candidate.get("level")
            doc_override = _normalise_optional_documents(candidate.get("documents"))
            milestone_override = _normalise_optional_milestones(
                candidate.get("milestones")
            )
        else:
            raw_terms = candidate
            classification = None
            reference = None
            level_override = None
            doc_override = []
            milestone_override = []

        try:
            terms = int(raw_terms)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"orbit entry at position {position} must define numeric 'terms'"
            ) from exc
        if terms < 2:
            raise ValueError("orbit entries require at least two terms")

        level = 1
        if level_override is not None:
            level = max(1, min(3, int(level_override)))
        else:
            if doc_override or doc_pool:
                level = 2
            if (milestone_override or milestone_pool) and classification in {
                "growing",
                "surging",
            }:
                level = 3

        docs_for_orbit: list[str] | None = doc_override or None
        if level >= 2:
            if not docs_for_orbit:
                if not doc_pool:
                    raise ValueError(
                        f"orbit '{reference or position}' requires documents for level {level}"
                    )
                window = max(1, min(len(doc_pool), level + 1))
                docs_for_orbit = doc_pool[:window]
        milestones_for_orbit: list[TimelineMilestone] | None = None
        if level >= 3:
            pool = milestone_override or milestone_pool
            if not pool:
                raise ValueError(
                    f"orbit '{reference or position}' requires milestones for level {level}"
                )
            milestones_for_orbit = pool
        elif milestone_override:
            milestones_for_orbit = milestone_override

        payload = progressive_complexity_suite(
            level,
            numeric_terms=terms,
            documents=docs_for_orbit,
            milestones=milestones_for_orbit,
            start=start_anchor,
        )

        entry_insights = payload.get("insights", [])
        reference_label = reference or f"orbit-{position}"
        entry = {
            "reference": reference_label,
            "terms": terms,
            "level": level,
            "classification": classification,
            "complexity_index": payload.get("complexity_index"),
            "insights": entry_insights[:3],
            "suite": payload,
        }
        results.append(entry)
        aggregate_complexity += float(payload.get("complexity_index", 0.0))
        levels.append(level)
        for insight in entry["insights"]:
            insights.append(f"[{reference_label}] {insight}")
        complexity_value = float(payload.get("complexity_index", 0.0))
        if complexity_value > peak_complexity:
            peak_complexity = complexity_value
            peak_reference = reference_label

    gradient = (
        results[-1]["complexity_index"] - results[0]["complexity_index"]
        if len(results) > 1
        else 0.0
    )
    summary = (
        f"Executed {len(results)} orbit(s) with aggregate complexity {aggregate_complexity:.2f}."
    )
    if peak_reference:
        summary += f" Peak complexity at {peak_reference}."

    return {
        "orbit_count": len(results),
        "orbits": results,
        "aggregate_complexity": round(aggregate_complexity, 3),
        "mean_level": round(sum(levels) / len(levels), 2),
        "complexity_gradient": round(float(gradient), 3),
        "peak_orbit": peak_reference,
        "insights": insights[:10],
        "summary": summary,
        "start_reference": _format_iso(start_anchor),
    }


def orchestrate_complexity_supercluster(program: Mapping[str, object]) -> dict[str, object]:
    """Fuse foundation, orbit, and escalation layers into a supercluster view."""

    if not isinstance(program, Mapping):
        raise ValueError("program must be a mapping of execution inputs")

    segments = program.get("segments")
    if segments is None:
        raise ValueError("program requires 'segments' to build the foundation")

    reference_prefix = str(program.get("reference_prefix", "segment"))
    foundation = construct_complexity_foundation(
        segments,
        reference_prefix=reference_prefix,
    )

    documents = _normalise_optional_documents(program.get("documents"))
    raw_milestones = program.get("milestones")
    milestone_pool = _normalise_optional_milestones(raw_milestones)
    start_value = program.get("start")
    start_dt = _ensure_datetime(start_value, None) if start_value is not None else None

    orbit_input = program.get("orbits") or foundation["segments"]
    orbit_payload = simulate_complexity_orbit(
        orbit_input,
        documents=documents or None,
        milestones=milestone_pool or None,
        start=start_dt,
    )

    signals = program.get("signals")
    escalation_payload: dict[str, object] | None = None
    if signals is not None:
        if not isinstance(signals, Mapping) or not signals:
            raise ValueError("signals must be a non-empty mapping when provided")
        capabilities = program.get("capabilities")
        events = program.get("events")
        initiatives = program.get("initiatives")
        escalation_payload = execute_feature_escalation(
            signals,
            capabilities=capabilities,
            events=events,
            initiatives=initiatives,
            start=start_dt,
        )

    total_score = foundation["momentum_average"] + orbit_payload["aggregate_complexity"]
    modules = ["foundation", "orbits"]
    if escalation_payload:
        total_score += float(escalation_payload.get("complexity_score", 0.0))
        modules.append("escalation")

    if total_score >= 45:
        grade = "supercluster"
    elif total_score >= 30:
        grade = "orbital"
    elif total_score >= 18:
        grade = "expansion"
    else:
        grade = "formation"

    summary = (
        f"Supercluster executed {' + '.join(modules)} layers with score {total_score:.2f}."
    )
    insights = list(foundation.get("insights", []))
    insights.extend(orbit_payload.get("insights", [])[:5])
    if escalation_payload:
        insights.extend(escalation_payload.get("insights", [])[:5])

    return {
        "grade": grade,
        "score": round(total_score, 3),
        "modules": modules,
        "foundation": foundation,
        "orbits": orbit_payload,
        "escalation": escalation_payload,
        "insights": insights[:12],
        "summary": summary,
    }


def synthesize_complexity_continuum(
    observations: Sequence[Mapping[str, object]] | Sequence[object],
    *,
    target: float | None = None,
) -> dict[str, object]:
    """Analyse sequential observations to measure momentum and stability."""

    if not isinstance(observations, Sequence) or len(observations) < 2:
        raise ValueError("at least two observations are required")

    clock = datetime.now(timezone.utc).replace(microsecond=0)
    normalised: list[dict[str, object]] = []
    for idx, entry in enumerate(observations):
        if isinstance(entry, Mapping):
            payload = dict(entry)
        else:
            raise ValueError(f"observation at index {idx} must be a mapping")

        timestamp_value = payload.get("timestamp") or payload.get("time") or payload.get("date")
        if timestamp_value is None:
            timestamp = clock + timedelta(days=idx)
        else:
            timestamp = _ensure_datetime(timestamp_value, None)

        complexity_value = None
        metrics = payload.get("metrics") if isinstance(payload.get("metrics"), Mapping) else None
        for key in (
            "complexity",
            "complexity_index",
            "score",
            "value",
        ):
            if key in payload:
                complexity_value = payload[key]
                break
            if metrics and key in metrics and complexity_value is None:
                complexity_value = metrics[key]
        if complexity_value is None:
            raise ValueError(f"observation at index {idx} missing complexity value")
        try:
            complexity = float(complexity_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"complexity value at index {idx} must be numeric") from exc
        if not isfinite(complexity):
            raise ValueError("complexity values must be finite")

        confidence_value = payload.get("confidence") or payload.get("confidence_score")
        if confidence_value is None and metrics and "confidence" in metrics:
            confidence_value = metrics["confidence"]
        confidence = 0.7
        if confidence_value is not None:
            try:
                confidence = float(confidence_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"confidence at index {idx} must be numeric") from exc
            confidence = max(0.0, min(1.0, confidence))

        normalised.append(
            {
                "timestamp": timestamp,
                "complexity": complexity,
                "confidence": round(confidence, 3),
                "label": str(payload.get("label") or payload.get("name") or "").strip() or None,
                "source": payload.get("source"),
                "notes": payload.get("insights") or payload.get("notes"),
            }
        )

    values = [entry["complexity"] for entry in normalised]
    for idx in range(1, len(normalised)):
        previous = normalised[idx - 1]
        current = normalised[idx]
        delta = current["complexity"] - previous["complexity"]
        elapsed_days = max(
            (current["timestamp"] - previous["timestamp"]).total_seconds() / 86400.0,
            1e-6,
        )
        velocity = delta / elapsed_days
        current["delta"] = round(delta, 3)
        current["velocity"] = round(velocity, 3)

    deltas = [entry.get("delta", 0.0) for entry in normalised[1:]]
    velocities = [entry.get("velocity", 0.0) for entry in normalised[1:]]
    momentum = sum(delta for delta in deltas if delta > 0)
    regression_events = [
        {
            "timestamp": _format_iso(normalised[idx]["timestamp"]),
            "delta": round(deltas[idx - 1], 3),
            "label": normalised[idx].get("label"),
        }
        for idx in range(1, len(normalised))
        if deltas[idx - 1] < 0
    ]
    velocity_mean = sum(velocities) / max(len(velocities), 1)
    velocity_peak = max(velocities, default=0.0)
    velocity_floor = min(velocities, default=0.0)
    stability = 1 / (1 + pstdev(values)) if len(values) > 1 else 1.0
    latest_delta = deltas[-1] if deltas else 0.0

    if velocity_mean > 0.3:
        trend = "accelerating"
    elif velocity_mean > 0.05:
        trend = "improving"
    elif velocity_mean < -0.2:
        trend = "contracting"
    elif velocity_mean < -0.05:
        trend = "softening"
    else:
        trend = "steady"

    projection: dict[str, object] | None = None
    if target is not None and velocity_mean > 0:
        remaining = target - values[-1]
        if remaining <= 0:
            projection = {"status": "achieved", "target": target}
        else:
            days_to_target = remaining / velocity_mean
            projection = {
                "status": "projected",
                "target": target,
                "eta_weeks": round(days_to_target / 7, 2),
            }
    elif target is not None:
        projection = {"status": "stalled", "target": target}

    observation_payload = []
    insights: list[str] = []
    for idx, entry in enumerate(normalised):
        payload = {
            "timestamp": _format_iso(entry["timestamp"]),
            "complexity": round(entry["complexity"], 3),
            "confidence": entry["confidence"],
        }
        if entry.get("label"):
            payload["label"] = entry["label"]
        if entry.get("delta") is not None and idx > 0:
            payload["delta"] = entry["delta"]
            payload["velocity"] = entry.get("velocity")
        if entry.get("notes"):
            payload["notes"] = entry["notes"]
        observation_payload.append(payload)
        if idx > 0 and entry.get("delta"):
            direction = "increased" if entry["delta"] > 0 else "declined"
            insights.append(
                f"{payload.get('label') or payload['timestamp']}: complexity {direction} "
                f"by {abs(entry['delta']):.2f}"
            )

    summary = (
        f"Continuum analysed {len(observation_payload)} observations; trend {trend} "
        f"with momentum {momentum:.2f}."
    )

    return {
        "observations": observation_payload,
        "momentum": round(momentum, 3),
        "velocity": {
            "mean": round(velocity_mean, 3),
            "peak": round(velocity_peak, 3),
            "floor": round(velocity_floor, 3),
        },
        "trend": {
            "classification": trend,
            "latest_delta": round(latest_delta, 3),
        },
        "stability_index": round(stability, 3),
        "regressions": regression_events[:5],
        "projection": projection,
        "insights": insights[:10],
        "summary": summary,
    }


def orchestrate_complexity_hyperdrive(program: Mapping[str, object]) -> dict[str, object]:
    """Amplify the supercluster output with a continuum momentum assessment."""

    if not isinstance(program, Mapping):
        raise ValueError("hyperdrive program must be a mapping")

    supercluster_payload = orchestrate_complexity_supercluster(program)

    continuum_input = program.get("continuum")
    observations: Sequence[Mapping[str, object]] | None = None
    target: float | None = None
    if isinstance(continuum_input, Mapping):
        obs_value = continuum_input.get("observations") or continuum_input.get("snapshots")
        if isinstance(obs_value, Sequence):
            observations = obs_value  # type: ignore[assignment]
        target_value = continuum_input.get("target")
        if target_value is not None:
            try:
                target = float(target_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("continuum target must be numeric") from exc
    if observations is None and "observations" in program:
        raw = program["observations"]
        if isinstance(raw, Sequence):
            observations = raw  # type: ignore[assignment]
    if observations is None:
        raise ValueError("program requires 'observations' for the hyperdrive continuum")

    continuum_payload = synthesize_complexity_continuum(observations, target=target)

    base_score = float(supercluster_payload.get("score", 0.0))
    continuum_score = continuum_payload["momentum"] + max(continuum_payload["velocity"]["mean"], 0) * 5
    total_score = base_score + continuum_score

    if total_score >= 70:
        grade = "hyperdrive"
    elif total_score >= 55:
        grade = "supercluster"
    elif total_score >= 40:
        grade = "orbital"
    else:
        grade = "formation"

    insights = list(supercluster_payload.get("insights", []))
    insights.extend(continuum_payload.get("insights", []))
    summary = (
        f"Hyperdrive fused supercluster score {base_score:.2f} with continuum momentum "
        f"{continuum_payload['momentum']:.2f} for total {total_score:.2f}."
    )

    return {
        "grade": grade,
        "score": round(total_score, 3),
        "supercluster": supercluster_payload,
        "continuum": continuum_payload,
        "insights": insights[:15],
        "summary": summary,
    }


def generate_complexity_observatory(spec: Mapping[str, object]) -> dict[str, object]:
    """Fuse signals, resilience, and capacity telemetry into a control-room view."""

    if not isinstance(spec, Mapping):
        raise ValueError("observatory specification must be a mapping")

    name = str(spec.get("name", "observatory")).strip() or "observatory"
    anchor = _ensure_datetime(spec.get("start"), None)
    timestamp = _format_iso(anchor or _normalise_datetime(None))
    target = float(spec.get("alignment_target", 0.75))
    resilience_horizon = float(spec.get("resilience_horizon_hours", 168.0))
    cycle_length = float(spec.get("cycle_length_days", 14.0))

    raw_signals = spec.get("signals")
    if raw_signals is not None and not isinstance(raw_signals, Mapping):
        raise ValueError("observatory 'signals' must be a mapping of alignment scores")
    signals_data = raw_signals if raw_signals else None

    raw_events = spec.get("events")
    if raw_events is not None and (
        isinstance(raw_events, (str, bytes)) or not isinstance(raw_events, Sequence)
    ):
        raise ValueError("observatory 'events' must be a sequence of resilience events")
    events_data = raw_events if raw_events else None

    raw_capacity = spec.get("team_capacity")
    if raw_capacity is not None and not isinstance(raw_capacity, Mapping):
        raise ValueError("observatory 'team_capacity' must be a mapping of hours")
    team_capacity = raw_capacity if raw_capacity else None

    raw_work = spec.get("work_items")
    if raw_work is not None and (
        isinstance(raw_work, (str, bytes)) or not isinstance(raw_work, Sequence)
    ):
        raise ValueError("observatory 'work_items' must be a sequence of task mappings")
    work_items = raw_work if raw_work else None

    coverage = {"signals": False, "resilience": False, "capacity": False}
    alignment_payload: dict[str, object] | None = None
    if signals_data:
        alignment_payload = assess_alignment_signals(signals_data, target=target)
        coverage["signals"] = True

    resilience_payload: dict[str, object] | None = None
    if events_data:
        resilience_payload = forecast_operational_resilience(
            events_data,
            start=anchor,
            horizon_hours=resilience_horizon,
        )
        coverage["resilience"] = True

    capacity_payload: dict[str, object] | None = None
    capacity_component: float | None = None
    if team_capacity and work_items:
        capacity_payload = plan_capacity_allocation(
            team_capacity,
            work_items,
            cycle_length_days=cycle_length,
        )
        summary = capacity_payload.get("summary", {})
        load_factor = summary.get("overall_load_factor") if isinstance(summary, Mapping) else None
        if load_factor is None or load_factor <= 1:
            capacity_component = 1.0
        else:
            capacity_component = max(0.0, min(1.0, 1 / float(load_factor)))
        coverage["capacity"] = True

    components: list[float] = []
    if alignment_payload:
        components.append(float(alignment_payload.get("average_score", 0.0)))
    if resilience_payload:
        components.append(float(resilience_payload.get("resilience_score", 0.0)))
    if capacity_component is not None:
        components.append(capacity_component)

    if not components:
        raise ValueError("observatory requires at least one populated telemetry source")

    observatory_index = sum(components) / len(components)
    status: str
    if observatory_index >= 0.78:
        status = "synchronised"
    elif observatory_index >= 0.6:
        status = "balancing"
    else:
        status = "stressed"

    insights: list[str] = []
    if alignment_payload and alignment_payload.get("classification") != "aligned":
        gap = float(alignment_payload.get("gap", 0.0))
        weakest = alignment_payload.get("focus", {}).get("weakest")
        focus = weakest or alignment_payload.get("signals", [{}])[-1].get("name")
        insights.append(
            f"Alignment gap of {gap:.3f} requires focus on {focus}"
        )
    if resilience_payload:
        risk = resilience_payload.get("risk", {})
        if isinstance(risk, Mapping) and risk.get("classification") != "stable":
            score = float(resilience_payload.get("resilience_score", 0.0))
            insights.append(
                f"Resilience stress classified as {risk.get('classification')} (score {score:.3f})"
            )
    if capacity_payload:
        summary = capacity_payload.get("summary", {})
        critical = summary.get("critical_teams") if isinstance(summary, Mapping) else None
        if critical:
            joined = ", ".join(str(team) for team in critical)
            insights.append(f"Capacity overload detected on {joined}")
        elif capacity_component is not None and capacity_component < 0.85:
            insights.append("Capacity load trending above comfort band")

    if alignment_payload and capacity_component is not None and capacity_component < 0.8:
        insights.append("Alignment gains risk stalling without capacity relief")

    return {
        "name": name,
        "timestamp": timestamp,
        "coverage": coverage,
        "alignment": alignment_payload,
        "resilience": resilience_payload,
        "capacity": capacity_payload,
        "observatory_index": round(observatory_index, 3),
        "status": status,
        "insights": insights[:10],
    }


def orchestrate_complexity_metaweb(program: Mapping[str, object]) -> dict[str, object]:
    """Create a multi-layer metaweb combining observatory, portfolio, and throughput data."""

    if not isinstance(program, Mapping):
        raise ValueError("metaweb program must be a mapping")

    name = str(program.get("name", "metaweb")).strip() or "metaweb"
    observatory_spec = program.get("observatory")
    if not isinstance(observatory_spec, Mapping):
        raise ValueError("metaweb program requires an 'observatory' mapping")

    observatory_payload = generate_complexity_observatory(observatory_spec)

    portfolio_payload: dict[str, object] | None = None
    portfolio_component: float | None = None
    if program.get("portfolio") is not None:
        portfolio_spec = program["portfolio"]
        if not isinstance(portfolio_spec, Mapping):
            raise ValueError("portfolio section must be a mapping")
        initiatives = portfolio_spec.get("initiatives")
        if not isinstance(initiatives, Sequence) or not initiatives:
            raise ValueError("portfolio initiatives must be a non-empty sequence")
        start = _ensure_datetime(portfolio_spec.get("start"), None)
        portfolio_payload = simulate_portfolio_outcomes(initiatives, start=start)
        portfolio_summary = portfolio_payload.get("portfolio", {})
        risk_index = float(portfolio_summary.get("risk_index", 0.0))
        portfolio_component = max(0.0, min(1.0, (3 - risk_index) / 2))

    throughput_payload: dict[str, object] | None = None
    throughput_component: float | None = None
    if program.get("throughput") is not None:
        throughput_spec = program["throughput"]
        if not isinstance(throughput_spec, Mapping):
            raise ValueError("throughput section must be a mapping")
        initiatives = throughput_spec.get("initiatives")
        if not isinstance(initiatives, Sequence) or not initiatives:
            raise ValueError("throughput initiatives must be a non-empty sequence")
        try:
            velocity = float(throughput_spec.get("velocity", 8.0))
            horizon = int(throughput_spec.get("horizon_weeks", 12))
        except (TypeError, ValueError) as exc:
            raise ValueError("throughput velocity and horizon must be numeric") from exc
        throughput_payload = forecast_portfolio_throughput(
            initiatives,
            velocity=velocity,
            horizon_weeks=horizon,
        )
        throughput_component = min(
            1.0,
            max(0.0, float(throughput_payload.get("confidence_projection", 0.0))),
        )

    components = [observatory_payload["observatory_index"]]
    breakdown = {"observatory": observatory_payload["observatory_index"]}
    if portfolio_component is not None:
        components.append(portfolio_component)
        breakdown["portfolio"] = round(portfolio_component, 3)
    if throughput_component is not None:
        components.append(throughput_component)
        breakdown["throughput"] = round(throughput_component, 3)

    meta_index = sum(components) / len(components)
    if meta_index >= 0.8:
        status = "cohesive"
    elif meta_index >= 0.62:
        status = "expanding"
    else:
        status = "turbulent"

    insights = list(observatory_payload.get("insights", []))
    if portfolio_payload:
        summary = portfolio_payload.get("portfolio", {})
        classification = summary.get("risk_classification")
        if classification and classification != "balanced":
            insights.append(
                f"Portfolio risk is {classification} with index {summary.get('risk_index')}"
            )
    if throughput_payload and throughput_component is not None and throughput_component < 0.7:
        insights.append(
            "Throughput confidence is below target; reinforce dependencies or velocity"
        )
    if portfolio_component is not None and throughput_component is not None:
        if portfolio_component > 0.8 and throughput_component < 0.6:
            insights.append("Strong portfolio design needs matching execution throughput")

    coverage = {
        "observatory": True,
        "portfolio": portfolio_payload is not None,
        "throughput": throughput_payload is not None,
    }

    return {
        "name": name,
        "meta_index": round(meta_index, 3),
        "status": status,
        "observatory": observatory_payload,
        "portfolio": portfolio_payload,
        "throughput": throughput_payload,
        "coverage": coverage,
        "components": breakdown,
        "insights": insights[:15],
    }


def orchestrate_complexity_multiverse(program: Mapping[str, object]) -> dict[str, object]:
    """Fuse multiple hyperdrive/metaweb streams into a multiverse portfolio signal."""

    if not isinstance(program, Mapping):
        raise ValueError("multiverse program must be a mapping")

    name = str(program.get("name", "multiverse")).strip() or "multiverse"
    universes = program.get("universes")
    if not isinstance(universes, Sequence) or not universes:
        raise ValueError("multiverse program requires a non-empty 'universes' sequence")

    raw_weights = program.get("weights")
    component_weights = {"hyperdrive": 0.45, "metaweb": 0.35, "observatory": 0.2}
    if raw_weights is not None:
        if not isinstance(raw_weights, Mapping):
            raise ValueError("weights must be a mapping of component names to numbers")
        for key in list(component_weights):
            if key in raw_weights:
                try:
                    value = float(raw_weights[key])
                except (TypeError, ValueError) as exc:
                    raise ValueError("weights must be numeric") from exc
                if value < 0:
                    raise ValueError("weights must be non-negative")
                component_weights[key] = value
    if not any(weight > 0 for weight in component_weights.values()):
        raise ValueError("at least one component weight must be positive")

    universes_payload: list[dict[str, object]] = []
    scoring: list[tuple[float, float]] = []
    coverage_flags = {"hyperdrive": False, "metaweb": False, "observatory": False}

    for idx, entry in enumerate(universes):
        if not isinstance(entry, Mapping):
            raise ValueError("each universe must be a mapping of inputs")
        universe_name = str(entry.get("name", f"universe-{idx + 1}")).strip() or f"universe-{idx + 1}"
        try:
            universe_weight = float(entry.get("weight", 1.0))
        except (TypeError, ValueError) as exc:
            raise ValueError("universe weight must be numeric") from exc
        if universe_weight <= 0:
            raise ValueError("universe weight must be positive")

        components: list[tuple[str, float]] = []
        component_breakdown: dict[str, float] = {}
        coverage = {"hyperdrive": False, "metaweb": False, "observatory": False}

        hyperdrive_payload: dict[str, object] | None = None
        metaweb_payload: dict[str, object] | None = None
        observatory_payload: dict[str, object] | None = None

        if entry.get("hyperdrive") is not None:
            hyperdrive_spec = entry["hyperdrive"]
            if not isinstance(hyperdrive_spec, Mapping):
                raise ValueError("hyperdrive section must be a mapping")
            hyperdrive_payload = orchestrate_complexity_hyperdrive(hyperdrive_spec)
            hyperdrive_score = max(0.0, min(1.0, float(hyperdrive_payload.get("score", 0.0)) / 100))
            components.append(("hyperdrive", hyperdrive_score))
            component_breakdown["hyperdrive"] = round(hyperdrive_score, 3)
            coverage["hyperdrive"] = True
            coverage_flags["hyperdrive"] = True

        if entry.get("metaweb") is not None:
            metaweb_spec = entry["metaweb"]
            if not isinstance(metaweb_spec, Mapping):
                raise ValueError("metaweb section must be a mapping")
            metaweb_payload = orchestrate_complexity_metaweb(metaweb_spec)
            metaweb_score = max(0.0, min(1.0, float(metaweb_payload.get("meta_index", 0.0))))
            components.append(("metaweb", metaweb_score))
            component_breakdown["metaweb"] = round(metaweb_score, 3)
            coverage["metaweb"] = True
            coverage_flags["metaweb"] = True

        if entry.get("observatory") is not None:
            observatory_spec = entry["observatory"]
            if not isinstance(observatory_spec, Mapping):
                raise ValueError("observatory section must be a mapping")
            observatory_payload = generate_complexity_observatory(observatory_spec)
            observatory_score = max(
                0.0,
                min(1.0, float(observatory_payload.get("observatory_index", 0.0))),
            )
            components.append(("observatory", observatory_score))
            component_breakdown["observatory"] = round(observatory_score, 3)
            coverage["observatory"] = True
            coverage_flags["observatory"] = True

        if not components:
            raise ValueError(
                f"universe '{universe_name}' requires at least one of hyperdrive, metaweb, or observatory"
            )

        weighted_sum = 0.0
        total_component_weight = 0.0
        for component_name, component_score in components:
            component_weight = component_weights.get(component_name, 0.0)
            if component_weight <= 0:
                continue
            weighted_sum += component_score * component_weight
            total_component_weight += component_weight
        if total_component_weight <= 0:
            raise ValueError("component weights must include at least one positive entry")
        index_value = weighted_sum / total_component_weight

        insights: list[str] = []
        for payload in (hyperdrive_payload, metaweb_payload, observatory_payload):
            if payload and isinstance(payload, Mapping):
                raw_insights = payload.get("insights")
                if isinstance(raw_insights, Sequence):
                    insights.extend(str(text) for text in raw_insights if str(text).strip())

        scoring.append((index_value, universe_weight))
        universe_status = "stellar" if index_value >= 0.82 else "expanding" if index_value >= 0.65 else "turbulent"
        universes_payload.append(
            {
                "name": universe_name,
                "index": round(index_value, 3),
                "weight": universe_weight,
                "status": universe_status,
                "components": component_breakdown,
                "hyperdrive": hyperdrive_payload,
                "metaweb": metaweb_payload,
                "observatory": observatory_payload,
                "coverage": coverage,
                "insights": insights[:12],
            }
        )

    total_weight = sum(weight for _, weight in scoring)
    multiverse_index = sum(score * weight for score, weight in scoring) / total_weight if total_weight else 0.0

    scores = [score for score, _ in scoring]
    if scores:
        mean_score = sum(scores) / len(scores)
        variance = sum((value - mean_score) ** 2 for value in scores) / len(scores)
        cohesion_index = max(0.0, 1.0 - min(1.0, math.sqrt(variance) * 3))
    else:  # pragma: no cover - defensive
        cohesion_index = 0.0

    if multiverse_index >= 0.82:
        status = "harmonic"
    elif multiverse_index >= 0.68:
        status = "aligned"
    else:
        status = "fragmented"

    insights: list[str] = []
    if universes_payload:
        sorted_universes = sorted(universes_payload, key=lambda item: item["index"], reverse=True)
        leader = sorted_universes[0]
        trailer = sorted_universes[-1]
        insights.append(
            f"{leader['name']} leads the multiverse with index {leader['index']} ({leader['status']})."
        )
        if leader is not trailer:
            insights.append(
                f"{trailer['name']} trails at {trailer['index']}; prioritize uplift to reduce divergence."
            )
    if cohesion_index < 0.6:
        insights.append("Cohesion is low; synchronize decision rhythms across universes.")
    elif cohesion_index > 0.85:
        insights.append("Cohesion is strong; leverage cross-universe playbooks for acceleration.")

    coverage = {name: flag for name, flag in coverage_flags.items()}

    return {
        "name": name,
        "multiverse_index": round(multiverse_index, 3),
        "status": status,
        "cohesion_index": round(cohesion_index, 3),
        "universes": universes_payload,
        "coverage": coverage,
        "weights": component_weights,
        "insights": insights[:15],
    }


def _normalise_optional_documents(value: object | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        candidates = [value]
    elif isinstance(value, Iterable):
        candidates = list(value)
    else:  # pragma: no cover - defensive
        raise ValueError("documents must be a string or iterable of strings")
    cleaned = [str(entry).strip() for entry in candidates if str(entry).strip()]
    return cleaned


def _normalise_optional_milestones(
    value: Sequence[Mapping[str, object]] | Sequence[TimelineMilestone] | None,
) -> list[TimelineMilestone]:
    if value is None:
        return []
    if isinstance(value, Sequence):
        candidates = value
    elif isinstance(value, Iterable):
        candidates = list(value)
    else:  # pragma: no cover - defensive
        raise ValueError("milestones must be a sequence")
    parsed: list[TimelineMilestone] = []
    for milestone in candidates:
        if isinstance(milestone, TimelineMilestone):
            parsed.append(milestone)
        elif isinstance(milestone, Mapping):
            parsed.append(TimelineMilestone.from_mapping(milestone))
        else:  # pragma: no cover - defensive
            raise ValueError("milestones must be mappings or TimelineMilestone instances")
    return parsed


def _coerce_sequence_of_mappings(value: object, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or not value:
        raise ValueError(f"{label} must be a non-empty sequence of objects")
    result: list[Mapping[str, object]] = []
    for idx, entry in enumerate(value):
        if isinstance(entry, Mapping):
            result.append(dict(entry))
        else:
            raise ValueError(f"{label} entry at index {idx} must be a mapping")
    return result


def _coerce_string_sequence(value: object, label: str) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, Sequence):
        candidates = [str(item) for item in value]
    else:
        raise ValueError(f"{label} must be a string or sequence of strings")
    cleaned = [text.strip() for text in candidates if text.strip()]
    if not cleaned:
        raise ValueError(f"{label} must include at least one non-empty entry")
    return cleaned


def _coerce_float_mapping(value: object, label: str) -> dict[str, float]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{label} must be a non-empty mapping")
    result: dict[str, float] = {}
    for key, raw in value.items():
        name = str(key).strip()
        if not name:
            raise ValueError(f"{label} keys must be non-empty strings")
        try:
            result[name] = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} value for {name!r} must be numeric") from exc
    return result
