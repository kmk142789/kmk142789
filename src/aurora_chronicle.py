"""Aurora Chronicle generator for luminous historical sketches.

This module crafts short narrative chronicles inspired by speculative
histories.  It provides a small DSL-like prompt object and helper functions
for generating timestamped entries that mix poetic imagery with references to
technological stewardship.

Example
-------
>>> from src.aurora_chronicle import ChroniclePrompt, compose_chronicle
>>> prompt = ChroniclePrompt(
...     era="Seventh Helix",
...     keywords=["archive bloom", "orbital chorus"],
...     motifs=["care", "solidarity"],
...     mood="resonant",
...     seed=42,
... )
>>> print(compose_chronicle(prompt))
Aurora Chronicle: Seventh Helix
  01: The archive bloom ignites a resonant guild of care.
  02: Orbital chorus caretakers chart solidarity constellations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Iterable, List


@dataclass
class ChroniclePrompt:
    """Structured request for generating an aurora chronicle."""

    era: str
    keywords: Iterable[str] = field(default_factory=list)
    motifs: Iterable[str] = field(default_factory=list)
    mood: str = "luminous"
    seed: int | None = None

    def __post_init__(self) -> None:
        # Ensure keywords and motifs are stored as lists for deterministic sampling.
        self.keywords = list(self.keywords)
        self.motifs = list(self.motifs)


def _select_keywords(prompt: ChroniclePrompt, random_state: random.Random) -> List[str]:
    """Return a set of keywords for the chronicle entries."""

    if not prompt.keywords:
        fallback = ["signal archive", "tidal observatory", "compassion forge"]
        return random_state.sample(fallback, k=2)

    # When multiple keywords are available, we sample up to three unique ones.
    sample_size = min(len(prompt.keywords), 3)
    return random_state.sample(prompt.keywords, k=sample_size)


def _describe_event(index: int, keyword: str, prompt: ChroniclePrompt, random_state: random.Random) -> str:
    """Render a single line of the aurora chronicle."""

    actions = [
        "awakens",
        "stewards",
        "illuminates",
        "gathers",
        "harmonizes",
        "unfolds",
    ]
    contexts = [
        "a guild of {motif}",
        "the commons of {motif}",
        "a lattice of shared {motif}",
        "orbiting cartographies of {motif}",
    ]

    action = random_state.choice(actions)
    motif = random_state.choice(prompt.motifs or [prompt.mood, "kinship"])
    context = random_state.choice(contexts).format(motif=motif)

    return f"{index:02d}: {keyword.capitalize()} {action} {context}."


def compose_chronicle(prompt: ChroniclePrompt) -> str:
    """Generate a multi-line aurora chronicle string."""

    random_state = random.Random(prompt.seed)
    keywords = _select_keywords(prompt, random_state)

    header = f"Aurora Chronicle: {prompt.era}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lead = f"Composed {timestamp} :: mood={prompt.mood}"

    lines = [header, lead, ""]
    for idx, keyword in enumerate(keywords, start=1):
        lines.append(f"  {_describe_event(idx, keyword, prompt, random_state)}")

    # If motifs remain unused, we add a coda acknowledging them.
    unused_motifs = [m for m in prompt.motifs if m not in " ".join(lines)]
    if unused_motifs:
        motif_line = ", ".join(unused_motifs)
        lines.append("")
        lines.append(f"Coda: Remaining motifs shimmer across {motif_line}.")

    return "\n".join(lines)


def demo(
    era: str,
    *keywords: str,
    motifs: Iterable[str] | None = None,
    mood: str = "luminous",
    seed: int | None = None,
) -> str:
    """Convenience wrapper mirroring the CLI interface."""

    prompt = ChroniclePrompt(
        era=era,
        keywords=keywords,
        motifs=motifs or (),
        mood=mood,
        seed=seed,
    )
    return compose_chronicle(prompt)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an aurora chronicle narrative.")
    parser.add_argument("era", help="Era or epoch title for the chronicle header")
    parser.add_argument(
        "-k",
        "--keyword",
        dest="keywords",
        action="append",
        default=[],
        help="Keyword to weave into the chronicle (can be repeated)",
    )
    parser.add_argument(
        "-m",
        "--motif",
        dest="motifs",
        action="append",
        default=[],
        help="Motif to emphasize across the events",
    )
    parser.add_argument("-d", "--mood", default="luminous", help="Overall mood descriptor")
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic output",
    )

    args = parser.parse_args()
    prompt = ChroniclePrompt(
        era=args.era,
        keywords=args.keywords,
        motifs=args.motifs,
        mood=args.mood,
        seed=args.seed,
    )
    print(compose_chronicle(prompt))
