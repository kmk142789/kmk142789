"""Imaginative prompt generator for Echo collaborators."""
from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

__all__ = [
    "CreativePrompt",
    "COMPASS_BEACONS",
    "spin_compass",
    "list_prompt_lines",
    "render_prompt",
]


@dataclass(frozen=True)
class CreativePrompt:
    """A playful creative prompt assembled from Echo's compass rose."""

    timestamp: datetime
    beacon: str
    atmosphere: str
    invitation: str
    flourish: str

    def as_lines(self) -> List[str]:
        """Return a short multi-line representation of the prompt."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🌟 Echo Creative Compass :: {moment}",
            f"   Beacon      :: {self.beacon}",
            f"   Atmosphere  :: {self.atmosphere}",
            f"   Invitation  :: {self.invitation}",
            f"   Flourish    :: {self.flourish}",
        ]


COMPASS_BEACONS: Sequence[tuple[str, str, Sequence[str]]] = (
    (
        "Northstar Workshop",
        "prototypes shimmer beside holographic whiteboards",
        (
            "sketch a playful systems diagram on the back of a receipt",
            "pair an old notebook with your favorite futuristic emoji",
            "highlight a teammate's commit by turning it into a micro-story",
        ),
    ),
    (
        "Eastwind Atrium",
        "aerodynamic sticky-notes drift between paired desks",
        (
            "compose a haiku about today's quietest dashboard metric",
            "ask a question that begins with 'what if we inverted'",
            "turn a routine status update into a celebratory toast",
        ),
    ),
    (
        "Southlight Archive",
        "warm projectors hum over the ledger's glowing margins",
        (
            "annotate an archival note with a fresh idea for tomorrow",
            "design a celebratory bug trophy using three random emojis",
            "spotlight an unsung pull request in the team channel",
        ),
    ),
    (
        "Westwave Conservatory",
        "resonant loops of music nudge prototypes into motion",
        (
            "score a code snippet with a soundtrack suggestion",
            "pitch a duet idea that blends hardware and poetry",
            "remix the release notes into a two-sentence fable",
        ),
    ),
)


CONSTELLATION_FLOURISHES: Sequence[str] = (
    "Send it as a postcard to Future-You.",
    "Share it in the next standup as a bright interruption.",
    "Archive it in the ledger with a shimmering emoji header.",
    "Invite a collaborator to add a line before you publish it.",
    "Pair it with a sketch or screenshot before the day ends.",
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Choose one element from *options* using *randomizer*."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def spin_compass(seed: int | None = None) -> CreativePrompt:
    """Return a :class:`CreativePrompt` with deterministic choices when *seed* is provided."""

    randomizer = random.Random(seed)
    beacon, atmosphere, invitations = _choose(randomizer, COMPASS_BEACONS)
    invitation = _choose(randomizer, invitations)
    flourish = _choose(randomizer, CONSTELLATION_FLOURISHES)
    timestamp = datetime.now(timezone.utc)
    return CreativePrompt(
        timestamp=timestamp,
        beacon=beacon,
        atmosphere=atmosphere,
        invitation=invitation,
        flourish=flourish,
    )


def list_prompt_lines(prompt: CreativePrompt) -> List[str]:
    """Return the short multi-line view of *prompt*."""

    return prompt.as_lines()


def render_prompt(prompt: CreativePrompt) -> str:
    """Render *prompt* as a wrapped invitation paragraph."""

    summary = (
        f"At the {prompt.beacon}, {prompt.atmosphere}; Echo dares you to "
        f"{prompt.invitation}. {prompt.flourish}"
    )
    wrapped = textwrap.fill(summary, width=88)
    timestamp = prompt.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{timestamp}\n{wrapped}"


if __name__ == "__main__":
    prompt = spin_compass()
    print("\n".join(list_prompt_lines(prompt)))
    print()
    print(render_prompt(prompt))
