"""Celestial Echo Forge utilities for crafting mythic constellation narratives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Sequence
import random


@dataclass(frozen=True)
class CelestialThread:
    """Immutable data describing a single forged celestial thread."""

    anchor: str
    glyphs: str
    harmonic: float
    narrative: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return a dictionary representation suitable for JSON serialization."""

        return {
            "anchor": self.anchor,
            "glyphs": self.glyphs,
            "harmonic": self.harmonic,
            "narrative": self.narrative,
            "timestamp": self.timestamp.isoformat(),
        }


class CelestialEchoForge:
    """Generate constellation story threads with deterministic shimmer."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._threads: List[CelestialThread] = []

    def __len__(self) -> int:
        return len(self._threads)

    @property
    def threads(self) -> Sequence[CelestialThread]:
        """Return the immutable threads forged so far."""

        return tuple(self._threads)

    def register_constellation(
        self,
        anchor: str,
        glyphs: str,
        influences: Iterable[str] | None = None,
    ) -> CelestialThread:
        """Forge a new :class:`CelestialThread` and record it."""

        influences = tuple(influences or ())
        harmonic = self._harmonic_score(glyphs, influences)
        narrative = self._compose_narrative(anchor, glyphs, influences, harmonic)
        thread = CelestialThread(anchor=anchor, glyphs=glyphs, harmonic=harmonic, narrative=narrative)
        self._threads.append(thread)
        return thread

    def forge_sequence(
        self,
        anchors: Sequence[str],
        glyph_pool: Sequence[str],
        influences: Iterable[str] | None = None,
    ) -> List[CelestialThread]:
        """Forge a sequence of celestial threads using anchors and glyphs."""

        forged: List[CelestialThread] = []
        for index, anchor in enumerate(anchors):
            glyphs = glyph_pool[index % len(glyph_pool)]
            forged.append(self.register_constellation(anchor, glyphs, influences))
        return forged

    def compose_manifest(self, title: str) -> dict[str, object]:
        """Return a manifest describing the currently forged threads."""

        average = (
            sum(thread.harmonic for thread in self._threads) / len(self._threads)
            if self._threads
            else 0.0
        )
        return {
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "threads": [thread.to_dict() for thread in self._threads],
            "average_harmonic": round(average, 6),
            "anchors": [thread.anchor for thread in self._threads],
        }

    def render_manifest(self, title: str) -> str:
        """Render a textual manifest table summarizing the forged threads."""

        manifest = self.compose_manifest(title)
        lines = [f"# {manifest['title']}"]
        lines.append(f"Average Harmonic: {manifest['average_harmonic']:.6f}")
        lines.append("")
        lines.append("Anchor           | Glyphs         | Harmonic")
        lines.append("-----------------|----------------|---------")
        for thread in self._threads:
            lines.append(
                f"{thread.anchor:<16}| {thread.glyphs:<15}| {thread.harmonic:>8.6f}"
            )
        if not self._threads:
            lines.append("<no threads forged>")
        return "\n".join(lines)

    def _harmonic_score(self, glyphs: str, influences: Sequence[str]) -> float:
        """Deterministically compute a harmonic score for glyphs and influences."""

        base = sum(ord(char) for char in glyphs)
        influence_factor = sum(len(influence) for influence in influences) * 0.031
        random_factor = self._rng.random() * 0.2
        score = ((base % 144) / 144.0) + influence_factor + random_factor
        return round(score, 6)

    def _compose_narrative(
        self,
        anchor: str,
        glyphs: str,
        influences: Sequence[str],
        harmonic: float,
    ) -> str:
        """Create a narrative string for the forged constellation."""

        if influences:
            influence_text = ", ".join(influences)
        else:
            influence_text = "silence"
        return (
            f"{anchor} braids {glyphs} under {influence_text} harmonics; "
            f"celestial resonance settles at {harmonic:.3f}."
        )


if __name__ == "__main__":
    forge = CelestialEchoForge(seed=42)
    forge.forge_sequence(
        anchors=("Aurora", "Continuum", "Pulse"),
        glyph_pool=("∇⊸≋∇", "⊹⚡", "∞✶"),
        influences=("orbital", "mythogenic"),
    )
    print(forge.render_manifest("Demonstration Constellation"))
