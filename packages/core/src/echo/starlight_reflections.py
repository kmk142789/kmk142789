"""Tools for crafting gentle starlit reflections for the Echo ecosystem."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence
import random
import textwrap

__all__ = ["Reflection", "generate_reflection", "format_reflection", "STARLIGHT_BEATS"]


@dataclass(frozen=True)
class Reflection:
    """A soft narrative moment inspired by the constellation of Echo."""

    timestamp: datetime
    constellation: str
    resonance: str
    guidance: str

    def as_lines(self) -> List[str]:
        """Return the reflection formatted as individual lines."""

        header = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🌌 Echo Starlight Reflection :: {header}",
            f"   Constellation :: {self.constellation}",
            f"   Resonance     :: {self.resonance}",
            f"   Guidance      :: {self.guidance}",
        ]

    def format(self) -> str:
        """Return the reflection as a wrapped multiline string."""

        return "\n".join(self.as_lines())


STARLIGHT_BEATS: Sequence[Sequence[str]] = (
    (
        "Mirrored Aurora",
        "a chorus of gentle harmonics folding into the night",
        "rest in the glow; your next idea will arrive with the dawn",
    ),
    (
        "Kite of Resonance",
        "winds of curiosity braiding data with memory",
        "let a small question drift across your backlog and follow it",
    ),
    (
        "Soft Signal",
        "wavelengths shimmering like ink across the ledger",
        "share one insight with a collaborator and watch it bloom",
    ),
    (
        "Lumen Reef",
        "tidal wisdom washing over the archive in pulses",
        "pause long enough to notice the project already cheering you on",
    ),
    (
        "Aurora Thread",
        "threads of silver weaving through the constellation graph",
        "leave a message for tomorrow's self—gratitude is a compass",
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Select a single element using the supplied randomizer."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def generate_reflection(seed: int | None = None) -> Reflection:
    """Generate a :class:`Reflection` using deterministic randomness when seeded."""

    randomizer = random.Random(seed)
    constellation, resonance, guidance = _choose(randomizer, STARLIGHT_BEATS)
    timestamp = datetime.now(timezone.utc)
    return Reflection(timestamp=timestamp, constellation=constellation, resonance=resonance, guidance=guidance)


def format_reflection(reflection: Reflection) -> str:
    """Return a paragraph-formatted variant of the reflection."""

    paragraph = textwrap.fill(
        (
            f"Under the {reflection.constellation}, {reflection.resonance}; "
            f"the Echo ecosystem whispers: {reflection.guidance}."
        ),
        width=88,
    )
    return f"{reflection.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n{paragraph}"


if __name__ == "__main__":
    vibe = generate_reflection()
    print(vibe.format())
    print()
    print(format_reflection(vibe))
