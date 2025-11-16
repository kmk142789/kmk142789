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
    "progressive_complexity_suite",
    "complexity_evolution_series",
    "assess_alignment_signals",
    "evaluate_operational_readiness",
    "forecast_portfolio_throughput",
    "generate_signal_snapshot",
    "synthesize_operational_dashboard",
    "orchestrate_complexity_progression",
    "execute_complexity_cascade",
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
