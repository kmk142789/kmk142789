"""Translate analysed ideas into actionable Echo plans."""

from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .idea_processor import IdeaAnalysis, IdeaProcessor

__all__ = ["IdeaActionStep", "IdeaActionPlan", "derive_action_plan"]


@dataclass(slots=True)
class IdeaActionStep:
    """Single actionable recommendation derived from an idea."""

    description: str
    priority: str
    confidence: float
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a serialisable representation of the step."""

        return {
            "description": self.description,
            "priority": self.priority,
            "confidence": round(_clamp(self.confidence), 3),
            "tags": list(self.tags),
        }


@dataclass(slots=True)
class IdeaActionPlan:
    """Structured plan that connects an idea to concrete follow ups."""

    idea: str
    analysis: IdeaAnalysis
    steps: tuple[IdeaActionStep, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialise the action plan to a dictionary."""

        return {
            "idea": self.idea,
            "analysis": {
                "word_count": self.analysis.word_count,
                "keywords": list(self.analysis.keywords),
                "sentiment": self.analysis.sentiment,
                "complexity": self.analysis.complexity,
                "density": self.analysis.density,
            },
            "steps": [step.to_dict() for step in self.steps],
        }

    def summary(self) -> str:
        """Return a short textual summary of the plan."""

        return (
            f"{len(self.steps)} steps derived — sentiment {self.analysis.sentiment}, "
            f"complexity {self.analysis.complexity:.3f}."
        )

    def to_markdown(self) -> str:
        """Render the plan as a Markdown document."""

        lines = [
            "# Idea to Action Plan",
            "",
            f"**Idea:** {self.idea}",
            f"**Sentiment:** {self.analysis.sentiment}",
            f"**Complexity:** {self.analysis.complexity:.3f}",
            f"**Lexical Density:** {self.analysis.density:.3f}",
            "",
            "## Recommended Steps",
        ]
        if not self.steps:
            lines.append("No actionable steps generated.")
            return "\n".join(lines)

        for index, step in enumerate(self.steps, start=1):
            tag_display = ", ".join(step.tags) if step.tags else "none"
            description = textwrap.fill(step.description, width=88)
            lines.append(
                f"{index}. {description} _(priority: {step.priority}, confidence: {step.confidence:.2f})_"
            )
            lines.append(f"   - Tags: {tag_display}")
        return "\n".join(lines)


def derive_action_plan(
    idea: str,
    *,
    max_steps: int = 3,
    rng_seed: int | None = None,
) -> IdeaActionPlan:
    """Convert ``idea`` into a deterministic action plan."""

    if max_steps <= 0:
        raise ValueError("max_steps must be positive")

    processor = IdeaProcessor(idea)
    analysis = processor.analyse()

    rng = random.Random(rng_seed)

    keywords = list(dict.fromkeys(analysis.keywords))
    if not keywords:
        keywords = _fallback_keywords(idea)

    focus = keywords[0] if keywords else "idea"
    supporting = keywords[1:] if len(keywords) > 1 else []

    density_boost = _clamp(0.55 + analysis.density * 0.35)
    complexity_boost = _clamp(0.5 + analysis.complexity * 0.3)

    templates = _build_step_templates(focus, supporting, analysis.sentiment)
    steps = []
    for priority, template in zip(_PRIORITIES, templates):
        confidence = _clamp(density_boost if priority == "high" else complexity_boost - 0.08 * len(steps))
        tags = (focus, *supporting[:2], priority)
        description = template(rng)
        steps.append(IdeaActionStep(description=description, priority=priority, confidence=confidence, tags=tags))
        if len(steps) >= max_steps:
            break

    if len(steps) < max_steps and supporting:
        remaining = max_steps - len(steps)
        for topic in supporting[:remaining]:
            description = (
                f"Map the resonance of “{topic}” into a measurable deliverable and log progress in the continuum registry."
            )
            steps.append(
                IdeaActionStep(
                    description=description,
                    priority="support",
                    confidence=_clamp(complexity_boost - 0.12 * len(steps)),
                    tags=(topic, "support"),
                )
            )

    return IdeaActionPlan(idea=idea, analysis=analysis, steps=tuple(steps[:max_steps]))


def _fallback_keywords(text: str) -> list[str]:
    import re

    tokens = re.findall(r"[\w']+", text.lower())
    unique: list[str] = []
    for token in tokens:
        if len(token) < 4:
            continue
        if token not in unique:
            unique.append(token)
    return unique[:5]


_PRIORITIES: Sequence[str] = ("high", "medium", "support")


def _build_step_templates(
    focus: str,
    supporting: Sequence[str],
    sentiment: str,
) -> Sequence[callable[[random.Random], str]]:
    """Prepare lazy templates that generate descriptions when invoked."""

    supporting_focus = supporting[0] if supporting else focus
    sentiment_tone = "celebrate" if "positive" in sentiment else "stabilise"

    def artifact_template(rng: random.Random) -> str:
        targets = ("docs", "artifacts", "data")
        location = rng.choice(targets)
        return (
            f"Translate the core insight around “{focus}” into a tangible {location} deliverable "
            "and record the context in the ledger."
        )

    def experiment_template(rng: random.Random) -> str:
        verbs = ("prototype", "script", "experiment")
        verb = rng.choice(verbs)
        return (
            f"Design a lightweight {verb} that demonstrates how “{supporting_focus}” advances the idea; "
            "capture inputs, outputs, and reproducibility notes."
        )

    def feedback_template(rng: random.Random) -> str:
        channels = ("Echo ledger", "MirrorJosh", "continuum reflection")
        channel = rng.choice(channels)
        return (
            f"{sentiment_tone.capitalize()} momentum by sharing a reflection with {channel} "
            f"and scheduling the next check-in on the created artifact."
        )

    return (artifact_template, experiment_template, feedback_template)


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value

