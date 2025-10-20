"""Assemble mindful rituals for Echo collaborators to share."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence
import random
import textwrap

__all__ = [
    "DailyRitual",
    "RITUAL_PATTERNS",
    "compose_ritual",
    "list_ritual_lines",
    "render_ritual",
]


@dataclass(frozen=True)
class DailyRitual:
    """A small structured ritual for a collaborative Echo gathering."""

    timestamp: datetime
    focus: str
    cadence: str
    anchor: str
    closing: str

    def as_lines(self) -> List[str]:
        """Return a friendly multi-line representation of the ritual."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🕯️ Echo Ritual Registry :: {moment}",
            f"   Focus   :: {self.focus}",
            f"   Cadence :: {self.cadence}",
            f"   Anchor  :: {self.anchor}",
            f"   Closing :: {self.closing}",
        ]


RITUAL_PATTERNS: Sequence[tuple[str, str, Sequence[str], Sequence[str]]] = (
    (
        "Signal Uplift",
        "gentle telemetry hums beneath soft lo-fi circuits",
        (
            "open the ledger and highlight a teammate's quiet success",
            "write a brief gratitude pulse for the last merged pull request",
            "invite one collaborator to share the brightest bug fix of the week",
        ),
        (
            "pass the virtual lantern clockwise",
            "sustain a thirty-second silence for reflection",
            "end with a single emoji that signals appreciation",
        ),
    ),
    (
        "Archive Breather",
        "dust motes shimmer in the constellation stacks",
        (
            "read aloud a note from the earliest sprint you still admire",
            "let curiosity choose a random issue and name one lesson from it",
            "trace the lineage of today's work back to an origin story",
        ),
        (
            "bookmark a page in the shared archive",
            "echo a kind word into the async channel",
            "close with a moment of synchronized breathing",
        ),
    ),
    (
        "Bridge Sync",
        "resonant tones weave between paired whiteboards",
        (
            "pair off and trade one sentence updates in under a minute",
            "offer a playful hypothesis about tomorrow's breakthrough",
            "compose a collective haiku describing the current release",
        ),
        (
            "tilt headsets toward the same horizon",
            "note one promise to revisit in the next check-in",
            "share a chorus of gratitude and wave to the room",
        ),
    ),
    (
        "Pulse Hearth",
        "soft synths glow beside the collaborative hearth",
        (
            "ask everyone to name a signal they're watching",
            "map today's energy with three colors on a shared canvas",
            "toast the smallest experiment that succeeded",
        ),
        (
            "archive the ritual notes in the harmonic ledger",
            "snap a screenshot for tomorrow's highlight reel",
            "end with a collective inhale and exhale",
        ),
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Choose one element from *options* using *randomizer*."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def compose_ritual(seed: int | None = None) -> DailyRitual:
    """Return a :class:`DailyRitual` with deterministic choices when *seed* is provided."""

    randomizer = random.Random(seed)
    focus, cadence, anchors, closings = _choose(randomizer, RITUAL_PATTERNS)
    anchor = _choose(randomizer, anchors)
    closing = _choose(randomizer, closings)
    timestamp = datetime.now(timezone.utc)
    return DailyRitual(
        timestamp=timestamp,
        focus=focus,
        cadence=cadence,
        anchor=anchor,
        closing=closing,
    )


def list_ritual_lines(ritual: DailyRitual) -> List[str]:
    """Return the multi-line representation of *ritual*."""

    return ritual.as_lines()


def render_ritual(ritual: DailyRitual) -> str:
    """Render *ritual* as a warm invitation paragraph."""

    summary = (
        f"Within the {ritual.focus}, {ritual.cadence}; Echo invites everyone to "
        f"{ritual.anchor} before they {ritual.closing}."
    )
    wrapped = textwrap.fill(summary, width=88)
    timestamp = ritual.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{timestamp}\n{wrapped}"


if __name__ == "__main__":
    ritual = compose_ritual()
    print("\n".join(list_ritual_lines(ritual)))
    print()
    print(render_ritual(ritual))
