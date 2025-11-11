"""Creative resonance generator for narrative experiments.

This module provides utilities to compose short pieces of text that blend
scientific language with imaginative imagery.  It can be used from the command
line or imported as a library.

The second iteration of the module introduces a richer internal model that
tracks structural decisions across calls.  A :class:`ResonanceContext` captures
random state, highlight weights, and derived metadata that guide sentence
rendering.  The context object can be serialised by applications that wish to
reuse the same creative scaffolding for multiple prompts.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
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
        return f"Context Map: motif orbit anchored entirely in {context.prompt.theme}."

    ranked = list(context.highlight_weights.items())[:3]
    descriptors = [f"{key} ({weight:.2f})" for key, weight in ranked]
    structures = ", ".join(context.structural_history)
    transition_count = len(context.transitions)
    return (
        "Context Map: highlights="
        + ", ".join(descriptors)
        + f" | structures={structures or 'n/a'} | transitions={transition_count}"
    )


def compose_resonance(prompt: ResonancePrompt) -> str:
    """Generate a multi-sentence resonance narrative."""

    context = _build_context(prompt)
    structure = _choose_structure(context.random_state)
    context.register_structure(structure)

    body: List[str] = []
    previous_kind: str | None = None
    for kind in structure:
        highlight = context.choose_highlight()
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
    return "\n".join([header, "", *body, "", footer])


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

    args = parser.parse_args()
    prompt = ResonancePrompt(
        theme=args.theme,
        highlights=args.highlights,
        tone=args.tone,
        seed=args.seed,
    )
    print(compose_resonance(prompt))
