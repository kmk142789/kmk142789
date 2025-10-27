"""Aurora Chronicle: a tiny generator for cosmic mini-stories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from random import choice, sample
from typing import Iterable, List


@dataclass(frozen=True)
class AuroraStory:
    """A structured story snippet with a title and lyrical body."""

    title: str
    body: str

    def format(self) -> str:
        """Render the story as a formatted block."""
        return f"{self.title}\n{'-' * len(self.title)}\n{self.body}"


def _choose(elements: Iterable[str], count: int) -> List[str]:
    """Return a list of unique elements drawn from *elements*."""

    population = list(dict.fromkeys(elements))
    count = max(1, min(len(population), count))
    return sample(population, count)


def craft_aurora_story(seed: str | None = None) -> AuroraStory:
    """Craft a new `AuroraStory` inspired by shimmering skylines."""

    constellations = (
        "Lyra", "Orion", "Cassiopeia", "Draco", "Phoenix", "Hydra", "Vela", "Auriga"
    )
    terrains = ("glacier", "desert", "tidal forest", "mirrored canyon", "cloud reef")
    artifacts = (
        "humming compass",
        "luminous quill",
        "resonant stone",
        "time-drift lantern",
        "polychrome prism",
    )
    emotions = (
        "quiet awe",
        "furious hope",
        "gentle defiance",
        "radiant curiosity",
        "playful resolve",
    )

    signature = seed if seed else choice(constellations)
    title = f"Aurora Chronicle — {signature}"
    fragments = _choose(constellations, 3)
    terrain = choice(terrains)
    relics = _choose(artifacts, 2)
    feeling = choice(emotions)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    body = (
        "In the {terrain} beneath {first}, {second} braided whispers with {third}.\n"
        "They carried a {relic_one} and a {relic_two}, trading secrets with auroral tides. "
        "The travelers moved with {feeling}, sketching luminous trails for tomorrow's dreamers.\n\n"
        "— logged at {timestamp}"
    ).format(
        terrain=terrain,
        first=fragments[0],
        second=fragments[1],
        third=fragments[2],
        relic_one=relics[0],
        relic_two=relics[1],
        feeling=feeling,
        timestamp=timestamp,
    )

    return AuroraStory(title=title, body=body)


def tell(seed: str | None = None) -> str:
    """Convenience wrapper returning the formatted story text."""

    return craft_aurora_story(seed).format()


if __name__ == "__main__":  # pragma: no cover
    print(tell())
