"""Progressively more complex analytical helpers for the Echo toolkit."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from statistics import pstdev
from typing import Iterable, Mapping, Sequence

__all__ = [
    "generate_numeric_intelligence",
    "analyze_text_corpus",
    "simulate_delivery_timeline",
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


def _normalise_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
