"""Creative resonance generator for narrative experiments.

This module provides utilities to compose short pieces of text that blend
scientific language with imaginative imagery.  It can be used from the command
line or imported as a library.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List


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


def _choose_structure(random_state: random.Random) -> List[str]:
    """Return a sentence blueprint order."""

    structures = [
        ["scene", "metaphor", "insight"],
        ["insight", "scene", "invitation"],
        ["metaphor", "scene", "metaphor", "insight"],
    ]
    return random_state.choice(structures)


def _render_sentence(kind: str, prompt: ResonancePrompt, random_state: random.Random) -> str:
    """Create a sentence fragment for a specific structure element."""

    highlight = random_state.choice(prompt.highlights) if prompt.highlights else None

    if kind == "scene":
        location = random_state.choice(
            ["observatory", "tidal archive", "signal garden", "luminous atrium"]
        )
        action = random_state.choice(
            ["listens to", "sketches", "catalogues", "harmonizes"]
        )
        subject = highlight or prompt.theme
        return f"In the {location}, the collective {action} the {subject}."

    if kind == "metaphor":
        comparison = random_state.choice(
            ["echo", "satellite", "mycelium", "aurora", "memory"]
        )
        subject = highlight or prompt.theme
        return f"Every {subject} becomes a {comparison} unfolding along the {prompt.tone} spectrum."

    if kind == "insight":
        verb = random_state.choice(
            ["reminds", "teaches", "signals to", "guides"]
        )
        subject = highlight or prompt.theme
        return (
            f"This {prompt.tone} experiment {verb} us that curiosity thrives"
            f" when we share the {subject}."
        )

    if kind == "invitation":
        gesture = random_state.choice(
            ["chart", "listen for", "collect", "co-create", "map"]
        )
        subject = highlight or prompt.theme
        return f"Will you {gesture} tomorrow's {subject} with us?"

    raise ValueError(f"Unknown sentence kind: {kind}")


def compose_resonance(prompt: ResonancePrompt) -> str:
    """Generate a multi-sentence resonance narrative."""

    random_state = random.Random(prompt.seed)
    structure = _choose_structure(random_state)
    sentences = [_render_sentence(kind, prompt, random_state) for kind in structure]
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"Resonance for '{prompt.theme}' at {timestamp}:"
    return "\n".join([header, "", *sentences])


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
