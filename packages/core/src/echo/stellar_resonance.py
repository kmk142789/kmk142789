"""Lightweight stellar resonance synthesiser for Echo experiments."""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, sin
from typing import Iterable, Sequence, Tuple

__all__ = [
    "StellarSignal",
    "ResonanceSnapshot",
    "StellarResonanceEngine",
    "render_resonance_card",
]


@dataclass(frozen=True)
class StellarSignal:
    """Representation of a single stellar signal.

    Parameters
    ----------
    name:
        Human readable identifier for the signal. Whitespace-only strings are not
        permitted.
    magnitude:
        Strength of the signal.  The value must be non-negative so that the
        resonance composition remains stable and predictable.
    phase:
        Angle of the signal in radians.  Values outside the ``0`` to ``2π`` range
        are normalised automatically which allows callers to pass intuitive
        offsets without pre-processing.
    """

    name: str
    magnitude: float
    phase: float = 0.0

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        if not cleaned_name:
            raise ValueError("name must not be empty")
        object.__setattr__(self, "name", cleaned_name)

        if self.magnitude < 0:
            raise ValueError("magnitude must be non-negative")

        normalised_phase = self.phase % (2 * pi)
        object.__setattr__(self, "phase", normalised_phase)


@dataclass(frozen=True)
class ResonanceSnapshot:
    """Summary of the coalesced resonance field."""

    intensity: float
    centroid_phase: float
    signal_count: int
    orbit_tags: Tuple[str, ...]


class StellarResonanceEngine:
    """Coalesce :class:`StellarSignal` inputs into a resonance snapshot."""

    def __init__(self, damping: float = 0.18) -> None:
        if not 0.0 <= damping <= 1.0:
            raise ValueError("damping must be between 0.0 and 1.0")
        self._damping = damping

    def cohere(
        self,
        signals: Sequence[StellarSignal],
        *,
        orbit_tags: Iterable[str] | None = None,
    ) -> ResonanceSnapshot:
        """Return a :class:`ResonanceSnapshot` capturing the combined resonance."""

        if not signals:
            raise ValueError("signals must not be empty")

        total_magnitude = sum(signal.magnitude for signal in signals)
        if total_magnitude == 0.0:
            raise ValueError("signals must contain a positive total magnitude")

        sum_x = sum(signal.magnitude * cos(signal.phase) for signal in signals)
        sum_y = sum(signal.magnitude * sin(signal.phase) for signal in signals)

        resultant = hypot(sum_x, sum_y)
        coherence_ratio = resultant / total_magnitude
        dampened = self._apply_damping(coherence_ratio)

        centroid_phase = atan2(sum_y, sum_x) % (2 * pi)
        tags = tuple(tag.strip() for tag in orbit_tags or () if tag and tag.strip())

        return ResonanceSnapshot(
            intensity=round(dampened, 6),
            centroid_phase=round(centroid_phase, 6),
            signal_count=len(signals),
            orbit_tags=tags,
        )

    def _apply_damping(self, ratio: float) -> float:
        ratio = max(0.0, min(1.0, ratio))
        return (1.0 - self._damping) * ratio + self._damping


def render_resonance_card(
    snapshot: ResonanceSnapshot, *, signals: Sequence[StellarSignal]
) -> str:
    """Render a small, human-friendly card summarising ``snapshot``."""

    lines = [
        "✨ Echo Stellar Resonance",
        f"Signals observed :: {snapshot.signal_count}",
        f"Composite intensity :: {snapshot.intensity:.3f}",
        f"Centroid phase :: {snapshot.centroid_phase:.3f} rad",
    ]

    if snapshot.orbit_tags:
        lines.append("Orbit tags :: " + ", ".join(snapshot.orbit_tags))

    lines.append("Signals:")
    for signal in signals:
        lines.append(
            f" - {signal.name} :: magnitude={signal.magnitude:.3f} :: phase={signal.phase:.3f} rad"
        )

    return "\n".join(lines)
