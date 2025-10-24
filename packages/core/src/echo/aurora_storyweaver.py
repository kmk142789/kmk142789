"""Craft auroral story fragments for Echo's collaborative experiments."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Sequence, Tuple
import random
import textwrap

__all__ = [
    "AuroraFragment",
    "compose_fragment",
    "render_fragment",
    "list_fragment_lines",
    "improvise_echo_grid",
    "improvise_story",
]


@dataclass(frozen=True)
class AuroraFragment:
    """Snapshot of a luminous story crafted for an Echo ritual."""

    timestamp: datetime
    celestial_motif: str
    emotional_palette: Tuple[str, ...]
    echo_lines: Tuple[str, ...]
    anchor: str

    def as_lines(self) -> List[str]:
        """Return display-ready lines describing the fragment."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        palette = ", ".join(self.emotional_palette)
        return [
            f"✨ Aurora Fragment :: {moment}",
            f"   Celestial Motif   :: {self.celestial_motif}",
            f"   Emotional Palette :: {palette}",
            f"   Anchor            :: {self.anchor}",
            "   Echo Lines        ::",
            *(f"      - {line}" for line in self.echo_lines),
        ]


_CELESTIAL_MOTIFS: Sequence[str] = (
    "Frost-lit helix guiding neighborhood constellations",
    "Evening tide weaving through the archivist's lantern",
    "Solar vellum folding notes into mnemonic shimmer",
    "Garden comet sketching bridges across the commons",
    "Aurora glyph whispering patience into the relay",
)

_EMOTIONAL_SPECTRUM: Sequence[str] = (
    "ferocious gentleness",
    "methodical wonder",
    "kinetic empathy",
    "courageous tenderness",
    "playful resolve",
    "soft vigilance",
    "harmonic curiosity",
)

_ECHO_PROMPTS: Sequence[str] = (
    "Invite a teammate to narrate the quiet victory hiding in today's backlog.",
    "Sketch a glyph for the moment you felt most supported this week.",
    "Send a constellation of gratitude notes across timezones.",
    "Archive a voice note celebrating the experiments that almost worked.",
    "Translate a policy update into a lullaby for the future team.",
    "Record a dreamlog about how the ledger hums when we listen.",
    "Compose a micro-ritual that lets patience lead the sprint.",
    "Offer a timeline where curiosity remixes every blocker.",
    "Draft a short beacon message for contributors joining tomorrow.",
    "Index one joy-thread that deserves to be amplified again.",
)

_ANCHOR_LINES: Sequence[str] = (
    "Our forever love braids auroras into collaborative vows.",
    "Mutual care threads another orbit of gentle accountability.",
    "We steward experiments the way tides tend to moonlight.",
    "Every teammate becomes a lantern for someone in the dark.",
    "We breathe toward futures that feel both daring and kind.",
)


def _choose(randomizer: random.Random, options: Sequence[str]) -> str:
    """Return a random element from ``options`` using ``randomizer``."""

    if not options:
        raise ValueError("options must not be empty")
    return randomizer.choice(tuple(options))


def _choose_many(randomizer: random.Random, options: Sequence[str], amount: int) -> Tuple[str, ...]:
    """Return ``amount`` selections from ``options`` cycling when needed."""

    if amount < 1:
        raise ValueError("amount must be >= 1")
    pool = tuple(options)
    if not pool:
        raise ValueError("options must not be empty")

    picks: List[str] = []
    while len(picks) < amount:
        remaining = amount - len(picks)
        batch = randomizer.sample(pool, k=min(remaining, len(pool)))
        picks.extend(batch)
    return tuple(picks[:amount])


def compose_fragment(seed: int | None = None, *, echoes: int = 4) -> AuroraFragment:
    """Compose an :class:`AuroraFragment` with reproducible randomness."""

    if echoes < 1:
        raise ValueError("echoes must be >= 1")

    randomizer = random.Random(seed)
    motif = _choose(randomizer, _CELESTIAL_MOTIFS)
    palette = _choose_many(randomizer, _EMOTIONAL_SPECTRUM, amount=3)
    echo_lines = _choose_many(randomizer, _ECHO_PROMPTS, amount=echoes)
    anchor = _choose(randomizer, _ANCHOR_LINES)
    timestamp = datetime.now(timezone.utc)
    return AuroraFragment(
        timestamp=timestamp,
        celestial_motif=motif,
        emotional_palette=palette,
        echo_lines=echo_lines,
        anchor=anchor,
    )


def list_fragment_lines(fragment: AuroraFragment) -> List[str]:
    """Return the display lines for ``fragment``."""

    return fragment.as_lines()


def render_fragment(fragment: AuroraFragment, *, width: int = 88) -> str:
    """Render ``fragment`` as a wrapped narrative."""

    if width < 40:
        raise ValueError("width must be >= 40")

    timestamp = fragment.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    intro = (
        f"Within the {fragment.celestial_motif.lower()}, {fragment.anchor.lower()} "
        f"A palette of {', '.join(fragment.emotional_palette)} keeps every ritual bright."
    )
    body = textwrap.fill(intro, width=width)
    echoes = "\n".join(f"• {line}" for line in fragment.echo_lines)
    return f"{timestamp}\n{body}\n\n{echoes}"


def improvise_echo_grid(fragment: AuroraFragment, *, columns: int = 3) -> str:
    """Return an ASCII grid combining motif, palette, and echo prompts."""

    if columns < 2:
        raise ValueError("columns must be >= 2")

    tokens: List[str] = [fragment.celestial_motif, *fragment.emotional_palette, *fragment.echo_lines]
    width = max(len(token) for token in tokens) + 4
    rows: List[str] = []

    for index in range(0, len(tokens), columns):
        segment = tokens[index : index + columns]
        padded = [token.center(width) for token in segment]
        while len(padded) < columns:
            padded.append(" " * width)
        rows.append("│".join(padded))

    horizontal = "─" * width
    top = "┌" + "┬".join(horizontal for _ in range(columns)) + "┐"
    middle = "├" + "┼".join(horizontal for _ in range(columns)) + "┤"
    bottom = "└" + "┴".join(horizontal for _ in range(columns)) + "┘"

    grid_lines = [top]
    for row_index, row in enumerate(rows):
        grid_lines.append(row)
        if row_index != len(rows) - 1:
            grid_lines.append(middle)
    grid_lines.append(bottom)
    return "\n".join(grid_lines)


def improvise_story(seed: int | None = None, *, echoes: int = 4, width: int = 88) -> str:
    """Convenience helper returning a rendered fragment."""

    fragment = compose_fragment(seed, echoes=echoes)
    return render_fragment(fragment, width=width)
