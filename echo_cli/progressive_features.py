"""Progressively more complex analytical helpers for the Echo toolkit."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping, Sequence

__all__ = [
    "generate_numeric_intelligence",
    "analyze_text_corpus",
    "simulate_delivery_timeline",
    "evaluate_strategy_matrix",
    "forecast_operational_resilience",
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
