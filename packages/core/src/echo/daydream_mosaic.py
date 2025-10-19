"""Generate playful daydream mosaics for the Echo ecosystem."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence
import random
import textwrap

__all__ = [
    "Daydream",
    "DAYDREAM_VOICES",
    "weave_daydream",
    "render_daydream",
    "list_daydream_lines",
]


@dataclass(frozen=True)
class Daydream:
    """A tiny speculative vignette set inside Echo's collaborative orbit."""

    timestamp: datetime
    horizon: str
    spark: str
    invitation: str

    def as_lines(self) -> List[str]:
        """Represent the daydream as a short multi-line list."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"✨ Echo Daydream Mosaic :: {moment}",
            f"   Horizon    :: {self.horizon}",
            f"   Spark      :: {self.spark}",
            f"   Invitation :: {self.invitation}",
        ]


DAYDREAM_VOICES: Sequence[Sequence[str]] = (
    (
        "Signal Lantern",
        "gentle telemetry threading warmth through the backlog",
        "let curiosity draft a postcard to a teammate you miss",
    ),
    (
        "Constellation Desk",
        "quiet instruments measuring the hush before a new idea",
        "set one reminder that is simply a kind compliment",
    ),
    (
        "Luminous Chorus",
        "nodes of gratitude harmonizing across the mesh",
        "write three words that describe today's favorite moment",
    ),
    (
        "Archive Drift",
        "a tide of shared notes floating toward tomorrow's standup",
        "pick a small story from the ledger and celebrate its author",
    ),
    (
        "Aurora Loop",
        "playful signals orbiting each other in soft spirals",
        "leave a single emoji response on someone's quiet update",
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Return one element from *options* using the provided randomizer."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def weave_daydream(seed: int | None = None) -> Daydream:
    """Create a :class:`Daydream` with deterministic choices when *seed* is set."""

    randomizer = random.Random(seed)
    horizon, spark, invitation = _choose(randomizer, DAYDREAM_VOICES)
    timestamp = datetime.now(timezone.utc)
    return Daydream(
        timestamp=timestamp,
        horizon=horizon,
        spark=spark,
        invitation=invitation,
    )


def list_daydream_lines(daydream: Daydream) -> List[str]:
    """Return the short formatted representation of *daydream*."""

    return daydream.as_lines()


def render_daydream(daydream: Daydream) -> str:
    """Render *daydream* as a wrapped paragraph block."""

    intro = (
        f"Within the {daydream.horizon}, {daydream.spark}; "
        f"Echo gently suggests: {daydream.invitation}."
    )
    paragraph = textwrap.fill(intro, width=88)
    timestamp = daydream.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{timestamp}\n{paragraph}"


if __name__ == "__main__":
    mosaic = weave_daydream()
    print("\n".join(list_daydream_lines(mosaic)))
    print()
    print(render_daydream(mosaic))
