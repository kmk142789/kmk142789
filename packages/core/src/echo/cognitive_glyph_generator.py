"""Cognitive Glyph Generator.

Transforms small numeric signal arrays into glyph sequences that can be
used in dashboards or textual summaries.  The generator stays deterministic
and does not mutate external state so it can be safely used within
EchoEvolver-style workflows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Sequence

from .evolver import _GLYPH_RING


@dataclass(frozen=True)
class GlyphSequence:
    """Container for a glyph band and its summary statistics."""

    glyphs: tuple[str, ...]
    mean_intensity: float
    volatility: float
    label: str | None = None

    def as_text(self) -> str:
        """Render the glyphs as a continuous string."""

        return "".join(self.glyphs)


class CognitiveGlyphGenerator:
    """Encode numeric signals as directional glyphs."""

    def __init__(self, glyph_ring: Sequence[str] | None = None) -> None:
        ring = tuple(glyph_ring) if glyph_ring is not None else tuple(_GLYPH_RING)
        if not ring:
            raise ValueError("glyph_ring must contain at least one glyph")
        self.glyph_ring = ring

    def _normalise_signal(self, value: float) -> float:
        scaled = 0.5 + 0.5 * math.tanh(value)
        return max(0.0, min(1.0, scaled))

    def generate(self, signals: Sequence[float], *, label: str | None = None) -> GlyphSequence:
        """Return a glyph sequence that mirrors the supplied signals."""

        if not signals:
            raise ValueError("signals must not be empty")

        normalised = [self._normalise_signal(value) for value in signals]
        glyphs = tuple(
            self.glyph_ring[min(len(self.glyph_ring) - 1, int(round(val * (len(self.glyph_ring) - 1))))]
            for val in normalised
        )

        return GlyphSequence(
            glyphs=glyphs,
            mean_intensity=mean(normalised),
            volatility=pstdev(normalised) if len(normalised) > 1 else 0.0,
            label=label,
        )

    def render_band(self, sequence: GlyphSequence, *, group: int = 4) -> str:
        """Return the glyphs grouped for human readability."""

        if group <= 0:
            group = len(sequence.glyphs)

        chunks = [
            "".join(sequence.glyphs[index : index + group])
            for index in range(0, len(sequence.glyphs), group)
        ]
        return " ".join(chunks)
