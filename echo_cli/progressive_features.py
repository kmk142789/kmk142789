"""Progressively more complex analytical helpers for the Echo toolkit."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Iterable, Mapping, Sequence

__all__ = [
    "generate_numeric_intelligence",
    "analyze_text_corpus",
    "simulate_delivery_timeline",
    "plan_capacity_allocation",
    "simulate_portfolio_outcomes",
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
