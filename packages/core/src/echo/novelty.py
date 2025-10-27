"""Utilities for generating playful novelty concepts.

This module intentionally keeps the mechanics lightweight so it can be used
both from automated scripts and interactive shells.  The generator leans on a
small curated palette of motifs and textures to synthesize combinations that
feel fresh without needing any external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import fill
from typing import List, Sequence
import random


@dataclass(frozen=True)
class NoveltySpark:
    """Represents a short narrative vignette produced by the generator."""

    title: str
    summary: str
    ingredients: Sequence[str]
    invitation: str

    def render(self, width: int = 88) -> str:
        """Pretty print the spark with gentle wrapping."""

        wrapped_summary = fill(self.summary, width=width)
        wrapped_invitation = fill(self.invitation, width=width)
        bullet_ingredients = "\n".join(f"    - {item}" for item in self.ingredients)
        return "\n".join(
            [
                f"Spark: {self.title}",
                f"Summary: {wrapped_summary}",
                "Ingredients:",
                bullet_ingredients,
                f"Invitation: {wrapped_invitation}",
            ]
        )


class NoveltyGenerator:
    """Composable generator that crafts novelty sparks.

    The generator keeps a palette of motifs grouped across three dimensions:
    textures, catalysts, and destinations.  Each spark blends elements from the
    palette, optionally weaving in a custom theme supplied by the caller.
    """

    _TEXTURES: Sequence[str] = (
        "kaleidoscopic",
        "luminous",
        "grainy analog",
        "nebula-soft",
        "crystalline",
        "holographic",
        "bioluminescent",
        "aurora-brushed",
    )

    _CATALYSTS: Sequence[str] = (
        "listening ritual",
        "sketchstorm",
        "signal garden",
        "midnight prototyping",
        "story collider",
        "hyperlocal exchange",
        "resonance walk",
        "microgravity rehearsal",
    )

    _DESTINATIONS: Sequence[str] = (
        "community experiment",
        "living mural",
        "open-source relic",
        "sonic postcard",
        "civic playtest",
        "immersive field note",
        "distributed zine",
        "satellite salon",
    )

    _INVITATIONS: Sequence[str] = (
        "pair up with a co-dreamer and explore how the idea could unfold over a weekend sprint",
        "collect three everyday artifacts that echo the concept and build a quick vignette",
        "prototype the feeling as a tiny soundscape, then invite others to remix it",
        "draft a manifesto paragraph that explains why this idea matters right now",
        "sketch the journey on paper, then translate it into your favourite medium",
        "host a fifteen-minute showcase circle to gather reflections",
        "document the first iteration and release it under a generous open license",
        "record a voice memo walking through the experience as if it already exists",
    )

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def _choose(self, options: Sequence[str]) -> str:
        return self._rng.choice(list(options))

    def _build_ingredients(self, theme: str | None) -> List[str]:
        palette = [
            f"{self._choose(self._TEXTURES)} atmosphere",
            f"{self._choose(self._CATALYSTS)} catalyst",
            f"{self._choose(self._DESTINATIONS)} outcome",
        ]
        if theme:
            palette.append(f"theme whisper: {theme}")
        # Ensure unique flavour while keeping order deterministic for readability.
        seen = set()
        unique_palette: List[str] = []
        for item in palette:
            if item not in seen:
                unique_palette.append(item)
                seen.add(item)
        return unique_palette

    def generate(self, *, count: int = 1, theme: str | None = None) -> List[NoveltySpark]:
        """Produce ``count`` sparks optionally guided by a thematic whisper."""

        if count <= 0:
            raise ValueError("count must be positive")

        sparks: List[NoveltySpark] = []
        for _ in range(count):
            title = self._compose_title(theme=theme)
            summary = self._compose_summary(theme=theme)
            ingredients = self._build_ingredients(theme)
            invitation = self._choose(self._INVITATIONS)
            sparks.append(
                NoveltySpark(
                    title=title,
                    summary=summary,
                    ingredients=ingredients,
                    invitation=invitation,
                )
            )
        return sparks

    def _compose_title(self, theme: str | None) -> str:
        texture = self._choose(self._TEXTURES).title()
        destination = self._choose(self._DESTINATIONS).title()
        if theme:
            return f"{texture} {theme.title()} {destination}"
        return f"{texture} {destination}"

    def _compose_summary(self, theme: str | None) -> str:
        catalyst = self._choose(self._CATALYSTS)
        destination = self._choose(self._DESTINATIONS)
        fragments: List[str] = [
            "Blend",
            catalyst,
            "with",
            destination,
            "to surface a playful space for shared imagination.",
        ]
        if theme:
            fragments.append(f"Let '{theme}' guide the tone of the experience.")
        return " ".join(fragments)


def generate_sparks(count: int = 1, theme: str | None = None, *, seed: int | None = None) -> List[NoveltySpark]:
    """Convenience helper that instantiates :class:`NoveltyGenerator` on demand."""

    rng = random.Random(seed) if seed is not None else None
    generator = NoveltyGenerator(rng=rng)
    return generator.generate(count=count, theme=theme)


__all__ = ["NoveltyGenerator", "NoveltySpark", "generate_sparks"]
