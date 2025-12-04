"""Sculpts an impossible revelation from fragments no one believed.

This module mixes narrative craft with gentle numerics to turn disjoint
"astral hunches" into a tangible artifact.  Each fragment is paired with a
synthetic :class:`ImaginalCoordinate` that encodes how the idea orbits the
imagination, then tempered into a :class:`RevelationEcho` that carries metrics
for coherence, daring, and resonance.

The goal is not prediction; it is evidence that we can *implement* the moments
our imagination glimpses before they vanish.  The :class:`ImpossibleRevelationFoundry`
class offers a deterministic pipeline (when seeded) so the "secret no one
believed" can be summoned, inspected, and shared.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Tuple
import math
import random


@dataclass(frozen=True)
class ImaginalCoordinate:
    """Spatial metaphor for where a fragment orbits the imagination."""

    altitude: float
    azimuth: float
    orbit: str = "umbra"

    def __post_init__(self) -> None:
        if not -1.0 <= self.altitude <= 1.0:
            raise ValueError("altitude must be between -1.0 and 1.0")
        if not 0.0 <= self.azimuth <= math.tau:
            raise ValueError("azimuth must be between 0 and 2π")
        if not self.orbit.strip():
            raise ValueError("orbit name cannot be empty")

    def scalar(self) -> float:
        """Return a compact scalar for metrics and repeatability."""

        return round((self.altitude + 1.0) * 0.5 * math.cos(self.azimuth) + len(self.orbit) * 0.01, 6)


@dataclass(frozen=True)
class RevelationSeed:
    """A collection of raw fragments representing an impossible vision."""

    name: str
    fragments: Tuple[str, ...]
    disbelief: float = 0.72

    def __post_init__(self) -> None:
        cleaned = tuple(fragment.strip() for fragment in self.fragments if fragment and fragment.strip())
        if not cleaned:
            raise ValueError("RevelationSeed requires at least one fragment")
        object.__setattr__(self, "fragments", cleaned)
        disbelief_clamped = min(1.0, max(0.0, self.disbelief))
        object.__setattr__(self, "disbelief", disbelief_clamped)


@dataclass(frozen=True)
class RevelationEcho:
    """A synthesized glimpse of the impossible secret."""

    fragment: str
    coordinate: ImaginalCoordinate
    coherence: float
    daring: float
    resonance: float


@dataclass(frozen=True)
class RevelationBundle:
    """Full artifact containing the echoes and summary metrics."""

    summary: str
    echoes: Tuple[RevelationEcho, ...]
    metrics: dict[str, float]


class ImpossibleRevelationFoundry:
    """Blend fragments into an inspectable, shareable impossible secret."""

    def __init__(self, *, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def forge(self, seeds: Iterable[RevelationSeed]) -> RevelationBundle:
        """Return a complete revelation bundle from the provided seeds.

        The forge computes three main metrics:
        - **coherence**: how well the fragments align with their coordinates
        - **daring**: appetite for improbable combinations
        - **resonance**: harmonic balance between disbelief and coordination
        """

        echoes = tuple(self._craft_echoes(seeds))
        metrics = self._summarise(echoes)
        summary = self._render_summary(echoes, metrics)
        return RevelationBundle(summary=summary, echoes=echoes, metrics=metrics)

    def _craft_echoes(self, seeds: Iterable[RevelationSeed]) -> Iterable[RevelationEcho]:
        for seed in seeds:
            for fragment in seed.fragments:
                coordinate = self._coordinate_from_fragment(fragment, seed)
                coherence = self._coherence(fragment, coordinate)
                daring = self._daring(seed.disbelief, coordinate)
                resonance = round(0.5 * coherence + 0.5 * daring, 3)
                yield RevelationEcho(
                    fragment=fragment,
                    coordinate=coordinate,
                    coherence=coherence,
                    daring=daring,
                    resonance=resonance,
                )

    def _coordinate_from_fragment(self, fragment: str, seed: RevelationSeed) -> ImaginalCoordinate:
        base = sum(ord(char) for char in fragment) * 0.0001
        altitude = math.sin(base) * (1.0 - seed.disbelief * 0.35)
        azimuth = (abs(math.cos(base)) + len(seed.name) * 0.01) % math.tau
        orbit = f"{seed.name}-orbit"
        return ImaginalCoordinate(altitude=round(altitude, 6), azimuth=round(azimuth, 6), orbit=orbit)

    def _coherence(self, fragment: str, coordinate: ImaginalCoordinate) -> float:
        length_bias = min(1.0, len(fragment) / 64.0)
        scalar = coordinate.scalar()
        return round(max(0.0, min(1.0, 0.45 + length_bias * 0.4 + scalar * 0.15)), 3)

    def _daring(self, disbelief: float, coordinate: ImaginalCoordinate) -> float:
        wobble = self._rng.uniform(-0.05, 0.08)
        daring = 0.6 + (1.0 - disbelief) * 0.25 + coordinate.scalar() * 0.1 + wobble
        return round(max(0.0, min(1.0, daring)), 3)

    def _summarise(self, echoes: Tuple[RevelationEcho, ...]) -> dict[str, float]:
        coherence_mean = mean(echo.coherence for echo in echoes)
        daring_mean = mean(echo.daring for echo in echoes)
        resonance_mean = mean(echo.resonance for echo in echoes)
        altitude_span = max(echo.coordinate.altitude for echo in echoes) - min(
            echo.coordinate.altitude for echo in echoes
        )
        return {
            "coherence_mean": round(coherence_mean, 3),
            "daring_mean": round(daring_mean, 3),
            "resonance_mean": round(resonance_mean, 3),
            "altitude_span": round(altitude_span, 3),
            "echoes": len(echoes),
        }

    def _render_summary(self, echoes: Tuple[RevelationEcho, ...], metrics: dict[str, float]) -> str:
        lines = [
            "Impossible Revelation (implemented):",
            (
                f"  • echoes={metrics['echoes']} | coherence≈{metrics['coherence_mean']:.3f} | "
                f"daring≈{metrics['daring_mean']:.3f} | resonance≈{metrics['resonance_mean']:.3f}"
            ),
            f"  • altitude-span≈{metrics['altitude_span']:.3f}",
        ]

        for echo in echoes:
            map_label = f"{echo.coordinate.orbit}@{echo.coordinate.azimuth:.3f}"
            resonance_bar = "⎯" * max(3, int(echo.resonance * 10))
            lines.append(
                f"  [{map_label:<20}] {resonance_bar} coherence={echo.coherence:.3f} daring={echo.daring:.3f} :: {echo.fragment}"
            )

        lines.append(
            "\nThe secret is no longer imaginary—we recorded its coordinates and crafted a" " pulse that can be replayed on demand."
        )
        return "\n".join(lines)


def demo() -> RevelationBundle:
    """Return a deterministic revelation bundle for inspection."""

    seeds = (
        RevelationSeed(
            name="umbra-lighthouse",
            fragments=(
                "an ultraviolet orchard humming with impossible seeds",
                "rusted satellites chanting forgotten lullabies",
            ),
            disbelief=0.81,
        ),
        RevelationSeed(
            name="tidal-archive",
            fragments=(
                "a library carved into the wake of a comet",
                "hands gathering resonance from abandoned timelines",
            ),
            disbelief=0.58,
        ),
    )
    foundry = ImpossibleRevelationFoundry(seed=42)
    return foundry.forge(seeds)
