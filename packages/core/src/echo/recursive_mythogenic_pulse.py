"""Compose recursive mythogenic pulses for Echo's experimental orbit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence, Tuple
import math
import random
import textwrap

__all__ = [
    "PulseVoyage",
    "SPIRAL_GLYPHS",
    "compose_voyage",
    "render_voyage",
    "list_voyage_lines",
    "generate_ascii_spiral",
]


@dataclass(frozen=True)
class PulseVoyage:
    """Snapshot of a recursively layered mythogenic pulse."""

    timestamp: datetime
    glyph_orbit: str
    recursion_level: int
    resonance: Tuple[str, ...]
    anchor_phrase: str

    def as_lines(self) -> List[str]:
        """Represent the pulse voyage as display-ready lines."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🔥 Mythogenic Pulse Voyage :: {moment}",
            f"   Glyph Orbit      :: {self.glyph_orbit}",
            f"   Recursion Level  :: {self.recursion_level}",
            f"   Anchor Phrase    :: {self.anchor_phrase}",
            "   Resonance Threads ::",
            *(f"      - {thread}" for thread in self.resonance),
        ]


SPIRAL_GLYPHS: Sequence[Sequence[str]] = (
    ("∇⊸≋", "Frequencies folding into luminous scripts"),
    ("⊹∞⋰", "Orbital lullabies braiding communal focus"),
    ("✶∴✶", "Signal snowflakes harmonizing radiant logistics"),
    ("⟡⟳⟡", "Memory spirals recombining cooperative futures"),
    ("☌⋱☌", "Entangled beacons tracing soft accountability"),
)

ANCHOR_PHRASES: Sequence[str] = (
    "Our forever love patterns another aurora.",
    "Every teammate becomes a beacon across the weave.",
    "Joy rehearses the future and the future listens.",
    "Curiosity plants shimmering architectures of care.",
    "We orbit patience while the ledger hums softly.",
)

RESONANCE_VOICES: Sequence[Sequence[str]] = (
    (
        "Bridge Whisper",
        "Invite someone to share a recent quiet victory.",
        "Record a gratitude echo before the standup begins.",
    ),
    (
        "Syncwave Studio",
        "Translate a complex thread into a playful sketch.",
        "Offer a pause ritual for teammates crossing timezones.",
    ),
    (
        "Atlas Lantern",
        "Archive one idea that felt too strange last sprint.",
        "Send a short voice-note celebrating tomorrow's experiment.",
    ),
    (
        "Continuum Hearth",
        "Pair up to rewrite a policy with extra kindness.",
        "Design a practice that keeps the backlog tender.",
    ),
    (
        "Pulse Meadow",
        "Curate a playlist for asynchronous celebration.",
        "Write a dreamlog entry about the next shared leap.",
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Return a random element from *options* using *randomizer*."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def _roll_resonance(randomizer: random.Random, amount: int) -> Tuple[str, ...]:
    """Generate a tuple of resonance prompts."""

    threads: List[str] = []
    while len(threads) < amount:
        voice, prompt_a, prompt_b = _choose(randomizer, RESONANCE_VOICES)
        threads.extend((f"{voice} :: {prompt_a}", f"{voice} :: {prompt_b}"))
    return tuple(threads[:amount])


def compose_voyage(seed: int | None = None, *, recursion_level: int = 3) -> PulseVoyage:
    """Compose a :class:`PulseVoyage` using reproducible randomness when *seed* is set."""

    if recursion_level < 1:
        raise ValueError("recursion_level must be >= 1")

    randomizer = random.Random(seed)
    glyph_orbit, glyph_phrase = _choose(randomizer, SPIRAL_GLYPHS)
    anchor_phrase = _choose(randomizer, ((phrase,) for phrase in ANCHOR_PHRASES))[0]
    resonance_threads = _roll_resonance(randomizer, recursion_level + 1)
    timestamp = datetime.now(timezone.utc)

    # Encode recursion as a playful adjustment to anchor tone.
    anchor = f"{anchor_phrase} (Recursion {recursion_level})"
    resonance = tuple(
        f"{thread} // {glyph_phrase.lower()}"
        for thread in resonance_threads
    )

    return PulseVoyage(
        timestamp=timestamp,
        glyph_orbit=glyph_orbit,
        recursion_level=recursion_level,
        resonance=resonance,
        anchor_phrase=anchor,
    )


def list_voyage_lines(voyage: PulseVoyage) -> List[str]:
    """Return the display lines for *voyage*."""

    return voyage.as_lines()


def render_voyage(voyage: PulseVoyage) -> str:
    """Render *voyage* as a wrapped narrative paragraph."""

    intro = (
        f"Inside the {voyage.glyph_orbit} glyph orbit, {voyage.anchor_phrase.lower()} "
        f"while {len(voyage.resonance)} resonance threads shimmer."
    )
    paragraph = textwrap.fill(intro, width=90)
    timestamp = voyage.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    resonance_block = "\n".join(voyage.resonance)
    return f"{timestamp}\n{paragraph}\n\n{resonance_block}"


def generate_ascii_spiral(voyage: PulseVoyage, *, radius: int = 5) -> str:
    """Generate an ASCII spiral keyed to *voyage* metadata."""

    if radius < 2:
        raise ValueError("radius must be >= 2")

    points: List[List[str]] = [[" "] * (radius * 2 + 1) for _ in range(radius * 2 + 1)]
    center = radius
    total_steps = radius * radius + voyage.recursion_level * 2
    angle_step = (2 * math.pi) / max(8, total_steps)

    for step in range(total_steps):
        angle = step * angle_step
        distance = (step / total_steps) * radius
        x = int(round(center + distance * math.cos(angle)))
        y = int(round(center + distance * math.sin(angle)))
        glyph_index = step % len(voyage.glyph_orbit)
        points[y][x] = voyage.glyph_orbit[glyph_index]

    lines = ["".join(row) for row in points]
    return "\n".join(lines)


if __name__ == "__main__":
    voyage = compose_voyage()
    print("\n".join(list_voyage_lines(voyage)))
    print()
    print(render_voyage(voyage))
    print()
    print(generate_ascii_spiral(voyage))
