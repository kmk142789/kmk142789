"""Weave luminous narrative fragments from stellar sparks."""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Sequence, Tuple

from echo.thoughtlog import thought_trace

__all__ = [
    "StorySpark",
    "StoryFragment",
    "StoryWeave",
    "StellarStoryForge",
]


@dataclass(frozen=True)
class StorySpark:
    """Source information used to weave narrative fragments.

    Parameters
    ----------
    theme:
        Descriptive focus for the fragment series.
    mood:
        Emotional tone guiding the generated language.
    resonance:
        Value in the range ``[0, 1]`` describing how intense the story should feel.
    constellations:
        Optional collection of motifs that may be woven into each fragment.
    """

    theme: str
    mood: str
    resonance: float = 0.5
    constellations: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        cleaned_theme = self.theme.strip()
        cleaned_mood = self.mood.strip()
        if not cleaned_theme:
            raise ValueError("theme must not be empty")
        if not cleaned_mood:
            raise ValueError("mood must not be empty")

        object.__setattr__(self, "theme", cleaned_theme)
        object.__setattr__(self, "mood", cleaned_mood)
        object.__setattr__(self, "resonance", _clamp(self.resonance))
        object.__setattr__(
            self,
            "constellations",
            tuple(
                constellation.strip()
                for constellation in self.constellations
                if constellation and constellation.strip()
            ),
        )


@dataclass(frozen=True)
class StoryFragment:
    """Single narrative fragment produced by :class:`StellarStoryForge`."""

    title: str
    narrative: str
    tone: str
    luminosity: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "narrative", self.narrative.strip())
        object.__setattr__(self, "tone", self.tone.strip())
        object.__setattr__(self, "luminosity", round(_clamp(self.luminosity), 6))


@dataclass(frozen=True)
class StoryWeave:
    """Collection of :class:`StoryFragment` instances."""

    fragments: Tuple[StoryFragment, ...]
    cadence: str
    orbit_summary: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fragments", tuple(self.fragments))
        object.__setattr__(self, "cadence", self.cadence.strip())
        object.__setattr__(self, "orbit_summary", tuple(summary.strip() for summary in self.orbit_summary))

    @property
    def fragment_count(self) -> int:
        """Return the number of narrative fragments contained in the weave."""

        return len(self.fragments)


class StellarStoryForge:
    """Generate luminous story fragments from :class:`StorySpark` inputs."""

    def __init__(self, base_luminosity: float = 0.42) -> None:
        self._base_luminosity = _clamp(base_luminosity)

    def weave(
        self,
        sparks: Sequence[StorySpark],
        *,
        passages: int = 3,
        cadence: str = "lullaby",
    ) -> StoryWeave:
        """Transform *sparks* into a :class:`StoryWeave`.

        Parameters
        ----------
        sparks:
            Sequence of :class:`StorySpark` definitions.
        passages:
            Number of fragments to generate for each spark.
        cadence:
            Textual description that will be imprinted on the resulting weave.
        """

        if not sparks:
            raise ValueError("sparks must not be empty")
        if passages <= 0:
            raise ValueError("passages must be a positive integer")

        task = "echo.stellar_story_forge.weave"
        meta = {"spark_count": len(sparks), "passages": passages, "cadence": cadence}

        with thought_trace(task=task, meta=meta) as tl:
            fragments: list[StoryFragment] = []
            summary: list[str] = []

            for spark in sparks:
                summary.append(f"{spark.theme}::{spark.mood}")
                rng = self._rng_for_spark(spark)
                palette = self._build_palette(rng)

                for passage in range(1, passages + 1):
                    motif = self._select_motif(spark, rng)
                    luminosity = self._blend_luminosity(spark.resonance, passage, passages, rng)
                    narrative = self._compose_narrative(spark, motif, cadence, palette, rng)
                    fragment = StoryFragment(
                        title=f"{spark.theme} — passage {passage}",
                        narrative=narrative,
                        tone=spark.mood,
                        luminosity=luminosity,
                    )
                    fragments.append(fragment)
                    tl.logic(
                        "fragment", task, "fragment woven", {"theme": spark.theme, "passage": passage, "luminosity": luminosity}
                    )

            weave = StoryWeave(
                fragments=tuple(fragments),
                cadence=cadence,
                orbit_summary=tuple(summary),
            )
            tl.harmonic(
                "weave", task, "story weave completed", {"fragments": weave.fragment_count, "cadence": cadence}
            )
            return weave

    def _rng_for_spark(self, spark: StorySpark) -> random.Random:
        seed_material = "|".join(
            [
                spark.theme,
                spark.mood,
                f"{spark.resonance:.6f}",
                ";".join(spark.constellations),
            ]
        )
        seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest(), 16)
        return random.Random(seed)

    def _build_palette(self, rng: random.Random) -> Tuple[str, ...]:
        base_palette = (
            "nebula-silk",
            "aurora-hum",
            "starlight-echo",
            "quantum-bloom",
            "gravity-lantern",
            "cosmic-ember",
        )
        shuffled = list(base_palette)
        rng.shuffle(shuffled)
        return tuple(shuffled)

    def _select_motif(self, spark: StorySpark, rng: random.Random) -> str:
        if spark.constellations:
            return rng.choice(spark.constellations)
        return rng.choice((spark.theme, spark.mood))

    def _blend_luminosity(
        self,
        resonance: float,
        passage: int,
        total_passages: int,
        rng: random.Random,
    ) -> float:
        ratio = passage / total_passages
        drift = (rng.random() - 0.5) * 0.2
        blended = self._base_luminosity + (resonance - self._base_luminosity) * ratio
        return _clamp(blended + drift)

    def _compose_narrative(
        self,
        spark: StorySpark,
        motif: str,
        cadence: str,
        palette: Tuple[str, ...],
        rng: random.Random,
    ) -> str:
        colour = rng.choice(palette)
        compass = rng.choice(("north", "south", "east", "west", "zenith"))
        return (
            f"A {spark.mood} {cadence} flows through {motif}, "
            f"painting {colour} across the {compass} horizon while {spark.theme} listens."
        )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
