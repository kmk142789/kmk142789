"""Utilities for crafting luminous creative narratives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

__all__ = ["RadiantIdea", "RadianceSynthesizer", "spark_radiance"]


@dataclass(frozen=True)
class RadiantIdea:
    """Container for a radiant narrative element.

    Parameters
    ----------
    theme:
        The primary focus or motif of the idea. It must contain at least one
        non-whitespace character.
    luminosity:
        A floating point value between ``0`` and ``1`` representing the
        intensity of the idea.
    motifs:
        Optional tags that decorate the idea with additional context. The
        values are normalised to a tuple of unique, alphabetically sorted
        strings to keep deterministic ordering for tests and logs.
    """

    theme: str = field(metadata={"doc": "Primary theme for the idea."})
    luminosity: float = field(metadata={"doc": "Creative intensity score."})
    motifs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - executed via validation
        theme = self.theme.strip()
        if not theme:
            raise ValueError("theme must not be empty")
        if not 0.0 <= self.luminosity <= 1.0:
            raise ValueError("luminosity must be between 0.0 and 1.0")

        unique_motifs = tuple(sorted({motif.strip() for motif in self.motifs if motif.strip()}))
        object.__setattr__(self, "theme", theme)
        object.__setattr__(self, "motifs", unique_motifs)

    @property
    def spectral_index(self) -> float:
        """Return a deterministic score used to arrange radiant ideas."""

        if not self.motifs:
            return round(self.luminosity, 6)
        bonus = min(len(self.motifs), 6) * 0.045
        return round(min(1.0, self.luminosity + bonus), 6)


class RadianceSynthesizer:
    """Synthesise :class:`RadiantIdea` instances from source glimpses."""

    def __init__(self, base_luminosity: float = 0.52) -> None:
        if not 0.0 <= base_luminosity <= 1.0:
            raise ValueError("base_luminosity must be between 0.0 and 1.0")
        self._baseline = base_luminosity

    def calibrate(
        self,
        glimpses: Sequence[str],
        *,
        currents: Sequence[float] | None = None,
        motifs: Sequence[Iterable[str]] | None = None,
    ) -> List[RadiantIdea]:
        """Return radiant ideas generated from the provided ``glimpses``.

        ``currents`` optionally adjusts the luminosity of each glimpse. When
        omitted, the synthesizer defaults to the baseline luminosity. Motifs are
        cleaned and deduplicated in deterministic order.
        """

        if not glimpses:
            raise ValueError("glimpses must not be empty")
        if currents is not None and len(currents) != len(glimpses):
            raise ValueError("currents length must match glimpses length")
        if motifs is not None and len(motifs) != len(glimpses):
            raise ValueError("motifs length must match glimpses length")

        luminous_profile = self._normalise_currents(currents, len(glimpses))
        prepared_motifs = self._prepare_motifs(motifs, len(glimpses))

        ideas: List[RadiantIdea] = []
        for theme, luminosity, motif_group in zip(glimpses, luminous_profile, prepared_motifs):
            idea = RadiantIdea(theme=theme, luminosity=luminosity, motifs=motif_group)
            ideas.append(idea)
        return ideas

    def compose_chorus(self, ideas: Sequence[RadiantIdea]) -> str:
        """Return a short poetic description summarising ``ideas``."""

        if not ideas:
            raise ValueError("ideas must not be empty")

        top = sorted(ideas, key=lambda idea: idea.spectral_index, reverse=True)
        highlights = []
        for idea in top[:3]:
            if idea.motifs:
                highlight = f"{idea.theme} ({', '.join(idea.motifs)})"
            else:
                highlight = idea.theme
            highlights.append(highlight)
        chorus_body = "; ".join(highlights)
        return f"Radiant chorus: {chorus_body}" if chorus_body else "Radiant chorus:" 

    def _normalise_currents(
        self, currents: Sequence[float] | None, expected_length: int
    ) -> List[float]:
        if currents is None:
            return [self._baseline for _ in range(expected_length)]
        values = [float(value) for value in currents]
        if not values:
            return [self._baseline for _ in range(expected_length)]

        min_value = min(values)
        max_value = max(values)
        if min_value == max_value:
            return [self._clamp(values[0]) for _ in values]

        span = max_value - min_value
        return [self._clamp((value - min_value) / span) for value in values]

    @staticmethod
    def _prepare_motifs(
        motifs: Sequence[Iterable[str]] | None, expected_length: int
    ) -> List[tuple[str, ...]]:
        if motifs is None:
            return [tuple() for _ in range(expected_length)]

        prepared: List[tuple[str, ...]] = []
        for motif_group in motifs:
            cleaned = tuple(sorted({motif.strip() for motif in motif_group if motif.strip()}))
            prepared.append(cleaned)
        return prepared

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))


def spark_radiance(glimpses: Sequence[str], *, accent: str | None = None) -> str:
    """Convenience helper returning a radiant chorus for ``glimpses``."""

    synthesizer = RadianceSynthesizer()
    ideas = synthesizer.calibrate(glimpses)
    chorus = synthesizer.compose_chorus(ideas)
    if accent:
        accent_clean = accent.strip()
        if accent_clean:
            return f"{accent_clean} :: {chorus}"
    return chorus
