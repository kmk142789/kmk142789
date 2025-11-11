"""Aurora Chronicle generator for luminous historical sketches.

This module crafts short narrative chronicles inspired by speculative
histories.  It provides a small DSL-like prompt object and helper functions
for generating timestamped entries that mix poetic imagery with references to
technological stewardship.

The implementation maintains compatibility with existing usage while adding
timeline tracking utilities for richer downstream integrations.  Generated
chronicles expose metadata describing motif coverage and lexical density so
callers can analyse how the narrative emphasised the supplied inputs.

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

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Iterable, List, Tuple


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


@dataclass
class ChronicleEvent:
    """Represent a single event within the chronicle."""

    keyword: str
    motif: str
    line: str


@dataclass
class ChronicleTimeline:
    """Container tracking generated events and motif coverage."""

    prompt: ChroniclePrompt
    events: List[ChronicleEvent] = field(default_factory=list)
    motif_usage: Counter[str] = field(default_factory=Counter)

    def add_event(self, keyword: str, motif: str, line: str) -> None:
        self.events.append(ChronicleEvent(keyword=keyword, motif=motif, line=line))
        self.motif_usage[motif] += 1

    def unused_motifs(self) -> List[str]:
        return [motif for motif in self.prompt.motifs if motif not in self.motif_usage]

    def lexical_density(self) -> float:
        if not self.events:
            return 0.0
        total_keywords = sum(len(event.keyword.split()) for event in self.events)
        unique_terms = len({token for event in self.events for token in event.keyword.split()})
        return round(unique_terms / total_keywords, 2)

    def render_metadata(self) -> str:
        motif_report = ", ".join(f"{motif}:{count}" for motif, count in self.motif_usage.items())
        density = self.lexical_density()
        return f"Motifs[{motif_report or 'none'}] | lexical_density={density}"


def _build_keyword_schedule(
    prompt: ChroniclePrompt, random_state: random.Random
) -> List[Tuple[str, str]]:
    """Return keyword/motif pairs for chronicle construction."""

    keywords = _select_keywords(prompt, random_state)
    motifs = list(prompt.motifs or [prompt.mood, "kinship"])
    if not motifs:
        motifs = [prompt.mood]

    schedule: List[Tuple[str, str]] = []
    for keyword in keywords:
        motif = random_state.choice(motifs)
        schedule.append((keyword, motif))
        if len(motifs) > 1:
            motifs = motifs[1:] + motifs[:1]
    return schedule


def _describe_event(
    index: int,
    keyword: str,
    motif: str,
    prompt: ChroniclePrompt,
    random_state: random.Random,
) -> Tuple[str, str]:
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
    context = random_state.choice(contexts).format(motif=motif)

    line = f"{index:02d}: {keyword.capitalize()} {action} {context}."
    return line, motif


def compose_chronicle(prompt: ChroniclePrompt) -> str:
    """Generate a multi-line aurora chronicle string."""

    random_state = random.Random(prompt.seed)
    timeline = ChronicleTimeline(prompt=prompt)
    schedule = _build_keyword_schedule(prompt, random_state)

    header = f"Aurora Chronicle: {prompt.era}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lead = f"Composed {timestamp} :: mood={prompt.mood}"

    lines = [header, lead, ""]
    for idx, (keyword, motif) in enumerate(schedule, start=1):
        line, used_motif = _describe_event(idx, keyword, motif, prompt, random_state)
        timeline.add_event(keyword, used_motif, line)
        lines.append(f"  {line}")

    # If motifs remain unused, we add a coda acknowledging them.
    unused_motifs = timeline.unused_motifs()
    if unused_motifs:
        motif_line = ", ".join(unused_motifs)
        lines.append("")
        lines.append(f"Coda: Remaining motifs shimmer across {motif_line}.")

    lines.append("")
    lines.append(f"Metadata: {timeline.render_metadata()}")

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
