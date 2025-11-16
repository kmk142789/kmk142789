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
    "assess_alignment_signals",
    "evaluate_operational_readiness",
    "forecast_portfolio_throughput",
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
