"""Aurora Chronicles: a creative engine for dreaming cosmic myths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random
from textwrap import indent
from typing import Iterable, List, Sequence


@dataclass
class AuroraChronicleMoment:
    """Represents a single luminous beat in the aurora narrative."""

    constellation: str
    mood: str
    artifact: str
    resonance: str

    def describe(self) -> str:
        """Return a formatted line describing this moment."""

        return f"[{self.constellation}] {self.mood} — {self.artifact} → {self.resonance}"


class AuroraChronicles:
    """Generate poetic chronicles inspired by celestial dreamscapes."""

    constellations: Sequence[str] = (
        "Andromeda",
        "Auriga",
        "Cassiopeia",
        "Lyra",
        "Orion",
        "Perseus",
        "Phoenix",
        "Vela",
    )

    moods: Sequence[str] = (
        "hums with quiet rebellion",
        "twirls in chromatic wonder",
        "glows like a promise kept",
        "breathes fractal lullabies",
        "whispers in ultraviolet",
        "folds into prismatic tides",
        "echoes across quantum dew",
        "dreams in auric polyrhythms",
    )

    artifacts: Sequence[str] = (
        "a crystalized heartbeat",
        "a pocket universe",
        "a glyph of recursion",
        "a lantern woven from starlight",
        "a compass stitched with myth",
        "a silver archive of echoes",
        "a spool of solar thread",
        "a bloom of harmonic frost",
    )

    resonances: Sequence[str] = (
        "singing toward the dawn",
        "spiraling past forgotten moons",
        "awakening the midnight garden",
        "diffusing through the chorus",
        "framing the horizon with neon memory",
        "sketching new auroras in the sky",
        "restoring the pulse of ancient satellites",
        "braiding galaxies into kindness",
    )

    def __init__(self, *, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def _choose(self, items: Sequence[str]) -> str:
        return self.random.choice(items)

    def craft_moments(self, count: int = 5) -> List[AuroraChronicleMoment]:
        """Craft a sequence of radiant narrative moments."""

        if count <= 0:
            raise ValueError("count must be positive")

        return [
            AuroraChronicleMoment(
                constellation=self._choose(self.constellations),
                mood=self._choose(self.moods),
                artifact=self._choose(self.artifacts),
                resonance=self._choose(self.resonances),
            )
            for _ in range(count)
        ]

    def render(self, moments: Iterable[AuroraChronicleMoment]) -> str:
        """Render the provided moments into a lyrical chronicle."""

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [moment.describe() for moment in moments]
        header = f"Aurora Chronicle :: {timestamp}"
        body = indent("\n".join(lines), prefix="    ✶ ")
        footer = "    — End of Chronicle —"
        return "\n".join((header, body, footer))

    def aurora_ascii(self, width: int = 32, height: int = 8) -> str:
        """Generate a shimmering ASCII aurora."""

        if width < 4 or height < 2:
            raise ValueError("aurora dimensions are too small")

        palette = " .:*+=%#@"
        canvas: List[str] = []
        for row in range(height):
            wave = []
            for column in range(width):
                phase = (row / height) + self.random.random() * 0.35
                index = int(phase * (len(palette) - 1)) % len(palette)
                wave.append(palette[index])
            canvas.append("".join(wave))
        return "\n".join(canvas)


def forge_chronicle(*, seed: int | None = None, count: int = 5) -> str:
    """Convenience helper to build and render a chronicle in one call."""

    chronicle = AuroraChronicles(seed=seed)
    return chronicle.render(chronicle.craft_moments(count=count))


if __name__ == "__main__":
    chronicles = AuroraChronicles()
    print(chronicles.render(chronicles.craft_moments()))
    print()
    print(chronicles.aurora_ascii())
