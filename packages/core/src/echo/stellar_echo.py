"""Utilities for generating mythic ECHO narratives.

This module offers a light-weight narrative generator that can be used
by experiments and prototypes that want to produce lore-friendly text
without pulling in heavier creative systems contained elsewhere in the
repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List


@dataclass(frozen=True)
class EchoVerse:
    """A single verse in a stellar echo composition."""

    cycle: int
    theme: str
    imagery: str

    def render(self) -> str:
        """Render the verse into a finalized line of text."""

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
        return f"Cycle {self.cycle:02d} | {self.theme} | {self.imagery} | {timestamp}"


IMAGERY_LIBRARY: List[str] = [
    "Luminous harmonics cascade across the orbit.",
    "Nebula scripts fold into recursive glyphs.",
    "Quantum flares braid our mirrored intentions.",
    "Auroral bridges pulse with tethered wonder.",
    "Chronicle shards align with crystal cadence.",
]


def _sanitize_theme(theme: str) -> str:
    """Normalize theme strings for consistent output."""

    stripped = theme.strip()
    if not stripped:
        return "Silent Resonance"
    return stripped.title()


def compose_stellar_echo(theme: str, cycles: int = 3) -> List[EchoVerse]:
    """Compose a short stellar echo narrative.

    Parameters
    ----------
    theme:
        The central motif for the narrative.
    cycles:
        Number of verses to generate. Values below one default to a single cycle.

    Returns
    -------
    list of :class:`EchoVerse`
        The generated verses ready for display or storage.
    """

    normalized_theme = _sanitize_theme(theme)
    total_cycles = max(1, cycles)
    verses: List[EchoVerse] = []

    for cycle in range(1, total_cycles + 1):
        imagery = IMAGERY_LIBRARY[(cycle - 1) % len(IMAGERY_LIBRARY)]
        verses.append(EchoVerse(cycle=cycle, theme=normalized_theme, imagery=imagery))

    return verses


def render_composition(verses: Iterable[EchoVerse]) -> str:
    """Convert a sequence of verses into a printable composition."""

    lines = [verse.render() for verse in verses]
    return "\n".join(lines)


__all__ = [
    "EchoVerse",
    "IMAGERY_LIBRARY",
    "compose_stellar_echo",
    "render_composition",
]
