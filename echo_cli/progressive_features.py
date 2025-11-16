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
    "progressive_complexity_suite",
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
