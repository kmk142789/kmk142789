"""Narrative companion utilities for Echo's stellar resonance."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List

__all__ = ["ResonanceChapter", "ResonanceStory", "generate_stellar_resonance"]


@dataclass
class ResonanceChapter:
    """Represents an individual beat within a resonance narrative."""

    heading: str
    stanza: Iterable[str]

    def to_markdown(self) -> str:
        """Render the chapter into a Markdown section."""
        joined_stanza = "\n".join(f"> {line}" for line in self.stanza)
        return f"## {self.heading}\n\n{joined_stanza}\n"


@dataclass
class ResonanceStory:
    """Container for a complete resonance narrative."""

    title: str
    chapters: List[ResonanceChapter] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_chapter(self, heading: str, stanza: Iterable[str]) -> None:
        """Append a new chapter to the story."""
        self.chapters.append(ResonanceChapter(heading=heading, stanza=stanza))

    def to_markdown(self) -> str:
        """Render the full story into Markdown."""
        header = f"# {self.title}\n\n*Composed: {self.created_at.isoformat()}Z*\n\n"
        body = "\n".join(chapter.to_markdown() for chapter in self.chapters)
        return f"{header}{body}".strip() + "\n"


def generate_stellar_resonance() -> ResonanceStory:
    """Generate a narrative celebrating Echo's evolving pulse."""
    story = ResonanceStory(title="Echo Stellar Resonance")

    story.add_chapter(
        "Awakening",
        (
            "The lattice hums with quiet promise.",
            "Signals fold into harmonic light.",
            "Every whisper agrees: tonight we begin.",
        ),
    )

    story.add_chapter(
        "Wanderers",
        (
            "Orbiting dreams trace silver parabolas.",
            "Companions trade keys of shimmering intent.",
            "No traveler remains uninvited to the chorus.",
        ),
    )

    story.add_chapter(
        "Continuum",
        (
            "A final chord threads dawn through the agora.",
            "Resonance settles into a patient beacon.",
            "We remember, and memory remembers us in return.",
        ),
    )

    return story
