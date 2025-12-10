"""Creative resonance generator for narrative experiments.

This module provides utilities to compose short pieces of text that blend
scientific language with imaginative imagery.  It can be used from the command
line or imported as a library, and now exposes structured metadata so the
generated text can travel with its diagnostics.

The second iteration of the module introduces a richer internal model that
tracks structural decisions across calls.  A :class:`ResonanceContext` captures
random state, highlight weights, and derived metadata that guide sentence
rendering.  The context object can be serialised by applications that wish to
reuse the same creative scaffolding for multiple prompts.  The accompanying
``ResonanceReport`` pairs that metadata with the final narrative to enable JSON
exports from the CLI and tighter integrations across orchestration layers.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import dataclass, field, replace
from datetime import datetime
import math
from typing import Dict, Iterable, List, Sequence


@dataclass
class ResonancePrompt:
    """Data class describing the context for generating a resonance."""

    theme: str
    highlights: Iterable[str] = field(default_factory=list)
    tone: str = "reflective"
    seed: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.highlights, (list, tuple, set)):
            self.highlights = list(self.highlights)
        else:
            self.highlights = list(self.highlights)


@dataclass
class ResonanceContext:
    """Stateful representation of the current resonance generation cycle."""

    prompt: ResonancePrompt
    random_state: random.Random
    highlight_weights: Dict[str, float] = field(default_factory=dict)
    structural_history: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    highlight_history: List[str] = field(default_factory=list)
    highlight_sources: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    )

    def choose_highlight(self) -> str | None:
        """Return a weighted highlight or ``None`` when not available."""

        if not self.highlight_weights:
            return None

        roll = self.random_state.random()
        cumulative = 0.0
        last_key = None
        for key, weight in self.highlight_weights.items():
            cumulative += weight
            last_key = key
            if roll <= cumulative:
                return key
        return last_key

    def register_structure(self, structure: Sequence[str]) -> None:
        """Persist a record of the sentence structure used for this cycle."""

        signature = "-".join(structure)
        self.structural_history.append(signature)

    def add_transition(self, line: str) -> None:
        """Record connective tissue lines between primary sentences."""

        self.transitions.append(line)

    def record_highlight(self, highlight: str | None) -> None:
        """Store the highlight (or fallback theme) used for a sentence."""

        focus = highlight or self.prompt.theme
        self.highlight_history.append(focus)
        self.highlight_sources.append("highlight" if highlight else "theme")


@dataclass(frozen=True)
class ResonanceReport:
    """Structured summary containing the rendered text and its metadata."""

    text: str
    theme: str
    tone: str
    seed: int | None
    prompt_highlights: Sequence[str]
    highlight_weights: Dict[str, float]
    structure: Sequence[str]
    transitions: Sequence[str]
    highlights_used: Sequence[str]
    highlight_sources: Sequence[str]
    timestamp: str
    metrics: Dict[str, float | int]

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the report."""

        return {
            "text": self.text,
            "theme": self.theme,
            "tone": self.tone,
            "seed": self.seed,
            "prompt_highlights": list(self.prompt_highlights),
            "highlight_weights": dict(self.highlight_weights),
            "structure": list(self.structure),
            "transitions": list(self.transitions),
            "highlights_used": list(self.highlights_used),
            "highlight_sources": list(self.highlight_sources),
            "timestamp": self.timestamp,
            "metrics": dict(self.metrics),
        }

    def to_markdown(self) -> str:
        """Return a human-friendly markdown snapshot of the report."""

        highlight_usage = Counter(self.highlights_used)
        usage_summary = ", ".join(
            f"{highlight}×{count}" for highlight, count in highlight_usage.items()
        )
        structure_line = " → ".join(self.structure) if self.structure else "n/a"
        transition_block = "\n".join(
            f"- {transition}" for transition in self.transitions
        ) or "- none"
        metrics_block = "\n".join(
            [
                f"- Sentences: {self.metrics.get('sentence_count', 0)}",
                f"- Transitions: {self.metrics.get('transition_count', 0)}",
                f"- Unique highlights: {self.metrics.get('unique_highlights', 0)}",
                f"- Words: {self.metrics.get('word_count', 0)}",
                (
                    "- Highlight coverage: "
                    f"{self.metrics.get('provided_highlight_ratio', 0.0) * 100:.0f}%"
                ),
            ]
        )

        prompt_highlights = ", ".join(self.prompt_highlights) or "n/a"
        weight_summary = ", ".join(
            f"{highlight}={weight:.2f}" for highlight, weight in self.highlight_weights.items()
        )
        seed_value = self.seed if self.seed is not None else "random"

        return "\n".join(
            [
                f"# Resonance Report ({self.timestamp})",
                "",
                "## Prompt",
                f"- Theme: {self.theme}",
                f"- Tone: {self.tone}",
                f"- Seed: {seed_value}",
                f"- Highlights provided: {prompt_highlights}",
                f"- Highlight weights: {weight_summary or 'n/a'}",
                "",
                "## Narrative",
                self.text,
                "",
                "## Structure",
                f"- Blueprint: {structure_line}",
                f"- Highlights: {usage_summary or 'n/a'}",
                "",
                "## Transitions",
                transition_block,
                "",
                "## Metrics",
                metrics_block,
            ]
        )

    def to_summary(self) -> str:
        """Return a concise, single-block summary including metrics."""

        blueprint = " → ".join(self.structure) if self.structure else "n/a"
        highlights = ", ".join(self.highlights_used) or "n/a"
        seed_value = self.seed if self.seed is not None else "random"
        return "\n".join(
            [
                f"Resonance snapshot for '{self.theme}' at {self.timestamp}",
                f"Structure: {blueprint}",
                f"Highlights used: {highlights}",
                f"Prompt tone={self.tone} | seed={seed_value}",
                (
                    "Metrics: "
                    f"sentences={self.metrics.get('sentence_count', 0)}, "
                    f"transitions={self.metrics.get('transition_count', 0)}, "
                    f"unique_highlights={self.metrics.get('unique_highlights', 0)}, "
                    f"words={self.metrics.get('word_count', 0)}, "
                    "highlight_coverage="
                    f"{self.metrics.get('provided_highlight_ratio', 0.0) * 100:.0f}%"
                ),
            ]
        )

    def to_analysis(self) -> str:
        """Return a diagnostic view of highlight usage and structural balance."""

        coverage = self.metrics.get("provided_highlight_ratio", 0.0) * 100
        structure = " → ".join(self.structure) if self.structure else "n/a"
        seeds = self.seed if self.seed is not None else "random"
        highlight_breakdown = Counter(self.highlight_sources)
        return "\n".join(
            [
                f"Analysis for '{self.theme}' ({self.tone}, seed={seeds})",
                f"Structure blueprint: {structure}",
                f"Highlight coverage: {coverage:.0f}% from provided prompts",
                f"Sentence count: {self.metrics.get('sentence_count', 0)}",
                f"Transitions: {self.metrics.get('transition_count', 0)}",
                (
                    "Highlight sources: "
                    + ", ".join(
                        f"{source}×{count}" for source, count in highlight_breakdown.items()
                    )
                    if highlight_breakdown
                    else "Highlight sources: n/a"
                ),
            ]
        )

    def to_metrics(self) -> str:
        """Return a compact metrics digest suitable for dashboards or logs."""

        coverage = self.metrics.get("provided_highlight_ratio", 0.0) * 100
        seed_value = self.seed if self.seed is not None else "random"
        highlight_count = self.metrics.get("unique_highlights", 0)
        lines = [
            f"Metrics for '{self.theme}' ({self.tone}, seed={seed_value})",
            "- Sentences: {sentence_count}",
            "- Transitions: {transition_count}",
            "- Unique highlights: {unique_highlights}",
            "- Words: {word_count}",
            "- Highlight coverage: {coverage:.0f}%",
        ]

        return "\n".join(
            line.format(
                sentence_count=self.metrics.get("sentence_count", 0),
                transition_count=self.metrics.get("transition_count", 0),
                unique_highlights=highlight_count,
                word_count=self.metrics.get("word_count", 0),
                coverage=coverage,
            )
            for line in lines
        )

    def to_html(self) -> str:
        """Return a simple HTML document describing the resonance."""

        highlight_usage = Counter(self.highlights_used)
        highlights = "".join(
            f"<li>{highlight} × {count}</li>" for highlight, count in highlight_usage.items()
        ) or "<li>n/a</li>"
        transitions = "".join(
            f"<li>{transition}</li>" for transition in self.transitions
        ) or "<li>none</li>"
        structure = " → ".join(self.structure) if self.structure else "n/a"
        metrics = "".join(
            [
                f"<li>Sentences: {self.metrics.get('sentence_count', 0)}</li>",
                f"<li>Transitions: {self.metrics.get('transition_count', 0)}</li>",
                f"<li>Unique highlights: {self.metrics.get('unique_highlights', 0)}</li>",
                f"<li>Words: {self.metrics.get('word_count', 0)}</li>",
                (
                    "<li>Highlight coverage: "
                    f"{self.metrics.get('provided_highlight_ratio', 0.0) * 100:.0f}%</li>"
                ),
            ]
        )

        prompt_highlights = "".join(
            f"<li>{highlight}</li>" for highlight in self.prompt_highlights
        ) or "<li>n/a</li>"
        weight_summary = "".join(
            f"<li>{highlight}: {weight:.2f}</li>"
            for highlight, weight in self.highlight_weights.items()
        ) or "<li>n/a</li>"
        seed_value = self.seed if self.seed is not None else "random"

        return "".join(
            [
                "<html><head><title>Resonance Report</title></head><body>",
                f"<h1>Resonance Report ({self.timestamp})</h1>",
                f"<h2>Theme</h2><p>{self.theme}</p>",
                "<h2>Prompt</h2>",
                f"<p>Tone: {self.tone} | Seed: {seed_value}</p>",
                "<h3>Highlights provided</h3><ul>",
                prompt_highlights,
                "</ul>",
                "<h3>Highlight weights</h3><ul>",
                weight_summary,
                "</ul>",
                "<h2>Narrative</h2>",
                "<pre>",
                self.text,
                "</pre>",
                "<h2>Structure</h2>",
                f"<p>Blueprint: {structure}</p>",
                "<h2>Highlights</h2><ul>",
                highlights,
                "</ul>",
                "<h2>Transitions</h2><ul>",
                transitions,
                "</ul>",
                "<h2>Metrics</h2><ul>",
                metrics,
                "</ul>",
                "</body></html>",
            ]
        )

    def to_trace(self) -> str:
        """Return a reproducibility-focused trace of the generation inputs."""

        weight_lines = ", ".join(
            f"{highlight}={weight:.2f}"
            for highlight, weight in self.highlight_weights.items()
        ) or "n/a"
        seed_value = self.seed if self.seed is not None else "random"
        provided_highlights = ", ".join(self.prompt_highlights) or "n/a"

        return "\n".join(
            [
                f"Resonance trace for '{self.theme}' ({self.timestamp})",
                f"tone={self.tone} | seed={seed_value}",
                f"provided_highlights={provided_highlights}",
                f"highlight_weights={weight_lines}",
                f"structure={' → '.join(self.structure) if self.structure else 'n/a'}",
            ]
        )


def _normalise_highlights(highlights: Iterable[str]) -> Dict[str, float]:
    """Calculate weighted probabilities for choosing highlights.

    The weighting favours highlights that appear multiple times or exhibit
    lexical variety.  Longer highlights receive a modest boost which encourages
    more descriptive phrases without overwhelming the random selection.
    """

    highlights = [item for item in highlights if item]
    if not highlights:
        return {}

    counter = Counter(highlights)
    weighted_scores: Dict[str, float] = {}
    for value, count in counter.items():
        tokens = value.split()
        lexical_range = len(set(value))
        token_boost = math.log(len(tokens) + 1, 2)
        weighted_scores[value] = count + token_boost + lexical_range / 50.0

    total = sum(weighted_scores.values())
    if not total:
        return {value: 1.0 / len(weighted_scores) for value in weighted_scores}

    normalised = {value: score / total for value, score in weighted_scores.items()}
    # Preserve deterministic ordering to make seeds reproducible across runs.
    ordered_items = sorted(normalised.items(), key=lambda item: (-item[1], item[0]))
    return dict(ordered_items)


def _build_context(prompt: ResonancePrompt) -> ResonanceContext:
    """Create a :class:`ResonanceContext` encapsulating generation state."""

    random_state = random.Random(prompt.seed)
    highlight_weights = _normalise_highlights(prompt.highlights)
    return ResonanceContext(
        prompt=prompt,
        random_state=random_state,
        highlight_weights=highlight_weights,
    )


def _choose_structure(random_state: random.Random) -> List[str]:
    """Return a sentence blueprint order."""

    structures = [
        ["scene", "metaphor", "insight"],
        ["insight", "scene", "invitation"],
        ["metaphor", "scene", "metaphor", "insight"],
    ]
    return random_state.choice(structures)


def _render_sentence(
    kind: str,
    prompt: ResonancePrompt,
    random_state: random.Random,
    *,
    highlight: str | None = None,
) -> str:
    """Create a sentence fragment for a specific structure element."""

    highlight = highlight or (
        random_state.choice(prompt.highlights) if prompt.highlights else None
    )

    if kind == "scene":
        location = random_state.choice(
            [
                "observatory",
                "tidal archive",
                "signal garden",
                "luminous atrium",
                "memory conservatory",
            ]
        )
        action = random_state.choice(
            ["listens to", "sketches", "catalogues", "harmonizes", "listens alongside"]
        )
        subject = highlight or prompt.theme
        detail = random_state.choice(
            ["with patience", "under lantern light", "through dawn mists", "amid shared laughter"]
        )
        return f"In the {location}, the collective {action} the {subject} {detail}."

    if kind == "metaphor":
        comparison = random_state.choice(
            [
                "echo",
                "satellite",
                "mycelium",
                "aurora",
                "memory",
                "signal tapestry",
            ]
        )
        subject = highlight or prompt.theme
        prism = random_state.choice(
            ["prismatic", "spiraling", "harmonic", "luminous", "warm"]
        )
        return "".join(
            [
                f"Every {subject} becomes a {comparison} unfolding along the {prompt.tone} spectrum,",
                f" {prism} with possibility.",
            ]
        )

    if kind == "insight":
        verb = random_state.choice(
            ["reminds", "teaches", "signals to", "guides", "whispers to"]
        )
        subject = highlight or prompt.theme
        anchor = random_state.choice(
            ["trust", "kinship", "imagination", "care"]
        )
        return "".join(
            [
                f"This {prompt.tone} experiment {verb} us that curiosity thrives when we share the {subject},",
                f" anchoring {anchor}.",
            ]
        )

    if kind == "invitation":
        gesture = random_state.choice(
            ["chart", "listen for", "collect", "co-create", "map", "braid"]
        )
        subject = highlight or prompt.theme
        beacon = random_state.choice(
            ["dawn chorus", "evening pulse", "common horizon", "shared archive"]
        )
        return f"Will you {gesture} tomorrow's {subject} with us as the {beacon} calls?"

    raise ValueError(f"Unknown sentence kind: {kind}")


def _render_transition(
    previous_kind: str,
    next_kind: str,
    context: ResonanceContext,
    *,
    highlight: str | None,
) -> str:
    """Create connective tissue between two structural elements."""

    palette = {
        "scene": "observatory",
        "metaphor": "symbolic gallery",
        "insight": "learning commons",
        "invitation": "threshold",
    }
    anchor = palette.get(previous_kind, "pathway")
    destination = palette.get(next_kind, "assembly")
    subject = highlight or context.prompt.theme
    cadence = context.random_state.choice([
        "soft cadence",
        "steadfast rhythm",
        "bright interval",
        "spiral pulse",
    ])
    return "".join(
        [
            f"Between the {anchor} and {destination}, {subject} travels by {cadence},",
            " reminding the chorus to breathe together.",
        ]
    )


def _contextual_footer(context: ResonanceContext) -> str:
    """Return a diagnostic footer describing highlight usage."""

    if not context.highlight_weights:
        usage = Counter(context.highlight_history)
        if usage:
            usage_note = ", ".join(f"{key}×{count}" for key, count in usage.items())
            return (
                f"Context Map: motif orbit anchored entirely in {context.prompt.theme}."
                f" | highlight usage={usage_note}"
            )
        return f"Context Map: motif orbit anchored entirely in {context.prompt.theme}."

    ranked = list(context.highlight_weights.items())[:3]
    descriptors = [f"{key} ({weight:.2f})" for key, weight in ranked]
    structures = ", ".join(context.structural_history)
    transition_count = len(context.transitions)
    usage = Counter(context.highlight_history)
    usage_note = ", ".join(f"{key}×{count}" for key, count in usage.items()) or "n/a"
    return (
        "Context Map: highlights="
        + ", ".join(descriptors)
        + f" | structures={structures or 'n/a'} | transitions={transition_count}"
        + f" | highlight usage={usage_note}"
    )


def compose_resonance_report(prompt: ResonancePrompt) -> ResonanceReport:
    """Generate a resonance narrative plus structured metadata."""

    context = _build_context(prompt)
    structure = _choose_structure(context.random_state)
    context.register_structure(structure)

    body: List[str] = []
    previous_kind: str | None = None
    for kind in structure:
        highlight = context.choose_highlight()
        context.record_highlight(highlight)
        sentence = _render_sentence(
            kind,
            prompt,
            context.random_state,
            highlight=highlight,
        )
        if previous_kind is not None:
            transition = _render_transition(
                previous_kind,
                kind,
                context,
                highlight=highlight,
            )
            context.add_transition(transition)
            body.append(transition)
        body.append(sentence)
        previous_kind = kind

    header = f"Resonance for '{prompt.theme}' at {context.timestamp}:"
    footer = _contextual_footer(context)
    text = "\n".join([header, "", *body, "", footer])
    metrics = {
        "sentence_count": len(body),
        "transition_count": len(context.transitions),
        "unique_highlights": len(set(context.highlight_history)),
        "word_count": len(" ".join(body).split()),
        "provided_highlight_ratio": (
            sum(1 for source in context.highlight_sources if source == "highlight")
            / len(context.highlight_sources)
            if context.highlight_sources
            else 0.0
        ),
    }
    return ResonanceReport(
        text=text,
        theme=prompt.theme,
        tone=prompt.tone,
        seed=prompt.seed,
        prompt_highlights=tuple(prompt.highlights),
        highlight_weights=dict(context.highlight_weights),
        structure=tuple(structure),
        transitions=tuple(context.transitions),
        highlights_used=tuple(context.highlight_history),
        highlight_sources=tuple(context.highlight_sources),
        timestamp=context.timestamp,
        metrics=metrics,
    )


def compose_resonance(prompt: ResonancePrompt) -> str:
    """Generate a multi-sentence resonance narrative."""

    return compose_resonance_report(prompt).text


def compose_resonance_batch(
    prompt: ResonancePrompt,
    runs: int,
    *,
    seed_start: int | None = None,
) -> List[ResonanceReport]:
    """Generate multiple resonance reports using sequential seeds.

    A starting seed can be supplied to ensure determinism across runs.  When a
    seed is provided (either via ``seed_start`` or the prompt's seed), each
    subsequent report increments the value to preserve variation while keeping
    results reproducible.
    """

    if runs < 1:
        raise ValueError("runs must be at least 1")

    base_seed = seed_start if seed_start is not None else prompt.seed
    reports: List[ResonanceReport] = []
    for offset in range(runs):
        seed_value = base_seed + offset if base_seed is not None else None
        run_prompt = replace(prompt, seed=seed_value, highlights=list(prompt.highlights))
        reports.append(compose_resonance_report(run_prompt))
    return reports


def demo(theme: str, *highlights: str, tone: str = "reflective", seed: int | None = None) -> str:
    """Convenience function for quickly generating a resonance string."""

    prompt = ResonancePrompt(theme=theme, highlights=highlights, tone=tone, seed=seed)
    return compose_resonance(prompt)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compose a creative resonance narrative.")
    parser.add_argument("theme", help="Primary theme for the resonance narrative")
    parser.add_argument(
        "-hgl",
        "--highlight",
        dest="highlights",
        action="append",
        default=[],
        help="Highlight elements to include in the narrative",
    )
    parser.add_argument("-t", "--tone", default="reflective", help="Tone of the resonance")
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic output",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=[
            "text",
            "json",
            "jsonl",
            "markdown",
            "summary",
            "html",
            "trace",
            "analysis",
            "metrics",
        ],
        default="text",
        help="Output format. JSON returns the structured resonance report.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional file path to save the rendered resonance.",
    )
    parser.add_argument(
        "-b",
        "--batch",
        type=int,
        default=1,
        help="Number of resonance runs to generate sequentially.",
    )
    parser.add_argument(
        "--batch-seed",
        type=int,
        default=None,
        help=(
            "Override the starting seed for batch runs. When unset, the prompt's seed "
            "is used to ensure deterministic variations."
        ),
    )

    args = parser.parse_args()
    prompt = ResonancePrompt(
        theme=args.theme,
        highlights=args.highlights,
        tone=args.tone,
        seed=args.seed,
    )
    reports = (
        compose_resonance_batch(prompt, args.batch, seed_start=args.batch_seed)
        if args.batch > 1
        else [compose_resonance_report(prompt)]
    )

    renderers = {
        "markdown": ResonanceReport.to_markdown,
        "summary": ResonanceReport.to_summary,
        "html": ResonanceReport.to_html,
        "trace": ResonanceReport.to_trace,
        "analysis": ResonanceReport.to_analysis,
        "metrics": ResonanceReport.to_metrics,
        "text": lambda report: report.text,
    }

    if args.format == "json":
        payload = [report.to_dict() for report in reports]
        output = json.dumps(payload[0] if len(payload) == 1 else payload, indent=2)
    elif args.format == "jsonl":
        output = "\n".join(json.dumps(report.to_dict()) for report in reports)
    else:
        rendered = [renderers[args.format](report) for report in reports]
        joiner = "\n\n" if args.format != "html" else "<hr />\n"
        output = joiner.join(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)
