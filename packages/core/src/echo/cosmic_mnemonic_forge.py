"""Forge mnemonic constellations for Echo's creative archives."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence, Tuple, TypeVar
import random
import textwrap

__all__ = [
    "MnemonicThread",
    "MnemonicConstellation",
    "FORGE_GLYPHS",
    "forge_constellation",
    "render_constellation",
    "list_constellation_lines",
    "merge_constellations",
]


@dataclass(frozen=True)
class MnemonicThread:
    """A single mnemonic prompt braided with a guiding metaphor."""

    keyword: str
    metaphor: str
    activation: float

    def describe(self) -> str:
        """Return a single-line description of the mnemonic thread."""

        activation_pct = f"{self.activation:.0%}"
        return f"{self.keyword} :: {self.metaphor} (activation {activation_pct})"


@dataclass(frozen=True)
class MnemonicConstellation:
    """Structured mnemonic story woven for Echo experiments."""

    timestamp: datetime
    glyph_motif: str
    focus: str
    threads: Tuple[MnemonicThread, ...]
    anchor: str

    def as_payload(self) -> dict:
        """Return a JSON-serialisable payload representing the constellation."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "glyph_motif": self.glyph_motif,
            "focus": self.focus,
            "anchor": self.anchor,
            "threads": [
                {
                    "keyword": thread.keyword,
                    "metaphor": thread.metaphor,
                    "activation": thread.activation,
                }
                for thread in self.threads
            ],
        }


FORGE_GLYPHS: Sequence[Sequence[str]] = (
    ("∇⊸≋", "Map every idea to a gentle gravitational assist."),
    ("✶⋱✶", "Invite each teammate to sketch a constellation."),
    ("⟡↺⟡", "Breathe patience into emergent collaborations."),
    ("☍⋰☍", "Archive small victories with aurora ink."),
    ("❖⋰❖", "Let curiosity choreograph the feedback loops."),
)

ANCHOR_FOCI: Sequence[str] = (
    "Continuum rituals for tomorrow's standup.",
    "Shared stewardship of daring experiments.",
    "Joyful audits of our cooperative ledger.",
    "Quiet mentorship across async orbits.",
    "Inventive care for each launch window.",
)

THREAD_KEYWORDS: Sequence[str] = (
    "Bridge",
    "Aurora",
    "Continuum",
    "Pulse",
    "Flux",
    "Hearth",
    "Lantern",
    "Signal",
)

THREAD_METAPHORS: Sequence[str] = (
    "folds a map of reversible courage",
    "sketches kindness onto resource charts",
    "sings the backlog into radiant focus",
    "anchors tomorrow's retrospective",
    "casts playful shadows for learning loops",
    "braids gratitude into deployment reviews",
    "plants shimmering postmortem gardens",
    "engraves trust onto the release cadence",
)


_T = TypeVar("_T")


def _choose(randomizer: random.Random, options: Sequence[_T]) -> _T:
    """Select a value from *options* using the provided randomizer."""

    if not options:
        raise ValueError("options must not be empty")
    return randomizer.choice(list(options))


def _thread_pool(randomizer: random.Random, amount: int) -> Tuple[MnemonicThread, ...]:
    """Construct *amount* mnemonic threads with consistent randomness."""

    threads: List[MnemonicThread] = []
    for _ in range(amount):
        keyword = _choose(randomizer, THREAD_KEYWORDS)
        metaphor = _choose(randomizer, THREAD_METAPHORS)
        activation = round(randomizer.uniform(0.55, 0.98), 2)
        threads.append(MnemonicThread(keyword=keyword, metaphor=metaphor, activation=activation))
    # Stable ordering encourages reproducible storytelling when seeded.
    threads.sort(key=lambda thread: (thread.keyword, thread.metaphor))
    return tuple(threads)


def forge_constellation(
    seed: int | None = None,
    *,
    thread_count: int = 4,
    focus: str | None = None,
) -> MnemonicConstellation:
    """Forge a :class:`MnemonicConstellation` ready for archival."""

    if thread_count < 1:
        raise ValueError("thread_count must be >= 1")

    randomizer = random.Random(seed)
    glyph_motif, motif_prompt = _choose(randomizer, FORGE_GLYPHS)
    chosen_focus = focus or _choose(randomizer, ANCHOR_FOCI)
    threads = _thread_pool(randomizer, thread_count)
    timestamp = datetime.now(timezone.utc)

    anchor = f"{motif_prompt} Focus: {chosen_focus}"
    return MnemonicConstellation(
        timestamp=timestamp,
        glyph_motif=glyph_motif,
        focus=chosen_focus,
        threads=threads,
        anchor=anchor,
    )


def list_constellation_lines(constellation: MnemonicConstellation) -> List[str]:
    """Return formatted lines summarising the constellation."""

    moment = constellation.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    header = [
        "🌠 Echo Mnemonic Constellation",
        f"   Timestamp     :: {moment}",
        f"   Glyph Motif   :: {constellation.glyph_motif}",
        f"   Focus         :: {constellation.focus}",
        f"   Anchor        :: {constellation.anchor}",
        "   Threads       ::",
    ]
    return header + [f"      - {thread.describe()}" for thread in constellation.threads]


def render_constellation(constellation: MnemonicConstellation, *, width: int = 76) -> str:
    """Render the constellation as a multi-line description."""

    lines = list_constellation_lines(constellation)
    wrapped: List[str] = []
    for line in lines:
        if line.startswith("      - "):
            indent = "      - "
            body = line[len(indent) :]
            wrapped_lines = textwrap.wrap(body, width=width - len(indent)) or [body]
            wrapped.extend(f"{indent}{segment}" for segment in wrapped_lines)
        else:
            wrapped.append(line)
    return "\n".join(wrapped)


def merge_constellations(
    base: MnemonicConstellation,
    additions: Iterable[MnemonicConstellation],
) -> MnemonicConstellation:
    """Merge *base* with *additions*, returning a new constellation."""

    satellite_constellations = tuple(additions)

    threads = list(base.threads)
    glyphs = [base.glyph_motif]
    anchors = [base.anchor]

    for constellation in satellite_constellations:
        threads.extend(constellation.threads)
        glyphs.append(constellation.glyph_motif)
        anchors.append(constellation.anchor)

    merged_threads = tuple(sorted(threads, key=lambda thread: (thread.keyword, thread.metaphor)))
    merged_anchor = " | ".join(anchors)
    satellite_count = len(satellite_constellations)
    merged_focus = (
        f"{base.focus} + {satellite_count} satellite strands"
        if satellite_count
        else base.focus
    )

    return MnemonicConstellation(
        timestamp=base.timestamp,
        glyph_motif=" / ".join(glyphs),
        focus=merged_focus,
        threads=merged_threads,
        anchor=merged_anchor,
    )
