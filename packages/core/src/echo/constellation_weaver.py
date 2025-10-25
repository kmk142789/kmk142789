"""Utilities for assembling small constellation narratives.

This module introduces the :func:`generate_constellation_weave` helper which can
be used by higher level creative systems to transform simple seed phrases into a
repeatable story scaffold.  The function is intentionally deterministic so that
it can be re-run to reproduce the same weave when given identical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, List, Sequence, Tuple


_LUMEN_PALETTE: Tuple[str, ...] = (
    "aurora",
    "nebula",
    "solstice",
    "quasar",
    "halo",
    "crescent",
    "radiance",
    "zenith",
)

_TEXTURE_PALETTE: Tuple[str, ...] = (
    "silk",
    "ember",
    "echo",
    "mycelium",
    "prism",
    "vapor",
    "lattice",
    "glyph",
)


@dataclass(frozen=True)
class ConstellationWeave:
    """Represents a small curated constellation narrative."""

    theme: str
    threads: Tuple[str, ...]
    pulse: str

    def render(self) -> str:
        """Render the weave as a human readable block of text."""

        header = f"Theme: {self.theme}"
        thread_lines = "\n".join(f"- {thread}" for thread in self.threads)
        pulse_line = f"Pulse: {self.pulse}"
        return "\n".join((header, thread_lines, pulse_line))


class ConstellationWeaverError(ValueError):
    """Raised when a weave cannot be created from the provided seeds."""


def _clean_seeds(seeds: Iterable[str]) -> List[str]:
    cleaned = [seed.strip() for seed in seeds if seed and seed.strip()]
    if not cleaned:
        raise ConstellationWeaverError("At least one non-empty seed is required")
    return cleaned


def _select_from_palette(seed: str, palette: Sequence[str]) -> str:
    digest = sha256(seed.encode("utf-8")).digest()
    index = digest[0] % len(palette)
    return palette[index]


def generate_constellation_weave(
    seeds: Iterable[str], *, theme: str, pulses: int = 3
) -> ConstellationWeave:
    """Create a deterministic :class:`ConstellationWeave` from the inputs.

    Args:
        seeds: Collection of seed phrases that describe the starting imagery.
        theme: High level summary that anchors the resulting weave.
        pulses: Number of narrative pulses that should be generated.

    Returns:
        :class:`ConstellationWeave` – a structured representation of the weave.

    Raises:
        ConstellationWeaverError: If validation fails for any reason.
    """

    if pulses < 1:
        raise ConstellationWeaverError("pulses must be a positive integer")

    if not theme or not theme.strip():
        raise ConstellationWeaverError("theme must be a non-empty string")

    cleaned_seeds = _clean_seeds(seeds)

    threads: List[str] = []
    for pulse_index in range(pulses):
        seed = cleaned_seeds[pulse_index % len(cleaned_seeds)]
        blend_source = f"{theme}|{seed}|{pulse_index}"
        tone = _select_from_palette(blend_source + "::tone", _LUMEN_PALETTE)
        texture = _select_from_palette(blend_source + "::texture", _TEXTURE_PALETTE)
        momentum = sha256((blend_source + "::momentum").encode("utf-8")).hexdigest()
        threads.append(
            f"{seed} — {tone} current, {texture} memory, spark {momentum[:8]}"
        )

    final_pulse_seed = "|".join(cleaned_seeds) + f"|{theme}|{pulses}"
    pulse_tone = _select_from_palette(final_pulse_seed, _LUMEN_PALETTE)
    pulse_texture = _select_from_palette(final_pulse_seed + "::texture", _TEXTURE_PALETTE)
    pulse = f"{pulse_tone} horizon braided with {pulse_texture} cadence"

    return ConstellationWeave(theme=theme.strip(), threads=tuple(threads), pulse=pulse)


__all__ = ["ConstellationWeave", "ConstellationWeaverError", "generate_constellation_weave"]
