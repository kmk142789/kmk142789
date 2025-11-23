"""Mythogenic resonance fingerprinting for time-series fragments.

This module introduces a lightweight but expressive signature generator that turns a
sequence of floating-point samples into a deterministic fingerprint.  The goal is to
surface a "world-first" view of how an Echo series is moving: velocity, curvature,
coherence, and an embellished glyph that encodes its current posture.  All
computations are deterministic and avoid external dependencies to keep the tool
portable across the wider Echo monorepo.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Iterable, Sequence


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _normalize(value: float, scale: float, *, clamp: bool = True) -> float:
    if scale == 0:
        return 0.0
    result = value / scale
    if not clamp:
        return result
    return max(0.0, min(1.0, result))


def _count_inversions(values: Sequence[float]) -> int:
    inversions = 0
    for left, right in zip(values[:-1], values[1:]):
        if left == 0 or right == 0:
            continue
        if (left > 0 > right) or (left < 0 < right):
            inversions += 1
    return inversions


@dataclass(frozen=True)
class ResonanceFingerprint:
    """Compact descriptor for a resonance slice."""

    baseline: float
    velocity: float
    curvature: float
    inversion_points: int
    coherence: float
    rarity: float
    glyph: str
    signature: str

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "baseline": round(self.baseline, 4),
            "velocity": round(self.velocity, 4),
            "curvature": round(self.curvature, 4),
            "inversion_points": self.inversion_points,
            "coherence": round(self.coherence, 4),
            "rarity": round(self.rarity, 4),
            "glyph": self.glyph,
            "signature": self.signature,
        }


def compute_resonance_fingerprint(
    series: Iterable[float], *, window: int = 5, label: str | None = None
) -> ResonanceFingerprint:
    """Compute a mythogenic fingerprint for the latest slice of ``series``.

    The fingerprint encodes directional motion (velocity), shape (curvature), and
    inversion hotspots (where the sign of change flips).  Two derived scores are added
    for operator use:

    - ``coherence`` measures how tight the windowed series is relative to the current
      baseline.  High coherence suggests a steady ritual; low coherence highlights
      volatility.
    - ``rarity`` rewards unique movement patterns: large acceleration, balanced
      inversions, and wide ranges all elevate the score.

    Parameters
    ----------
    series:
        Iterable of numeric samples.
    window:
        Window length to consider when computing the fingerprint.  Defaults to 5.
    label:
        Optional label seeded into the signature hash for reproducibility across runs.
    """

    values = [float(value) for value in series]
    if not values:
        return ResonanceFingerprint(0.0, 0.0, 0.0, 0, 0.0, 0.0, "⌀", "0" * 12)

    window = max(2, window)
    windowed = values[-window:]
    baseline = windowed[-1]

    deltas = [b - a for a, b in zip(windowed[:-1], windowed[1:])]
    velocity = _mean(deltas)
    second_order = [b - a for a, b in zip(deltas[:-1], deltas[1:])]
    curvature = _mean(second_order)
    inversions = _count_inversions(deltas) if len(deltas) >= 2 else 0

    amplitude = max(windowed) - min(windowed)
    coherence_scale = abs(baseline) + amplitude or 1.0
    coherence = 1.0 - _normalize(amplitude, coherence_scale)

    rarity_basis = abs(curvature) + abs(velocity) * 0.5
    rarity = _normalize(rarity_basis + inversions * 0.15, amplitude + 1.5)

    velocity_band = int(round(_normalize(abs(velocity), amplitude + 1.0) * 4))
    curvature_band = int(round(_normalize(abs(curvature), amplitude + 1.0) * 4))
    inversion_band = min(4, inversions)
    glyph_alphabet = ["⟁", "⌖", "✶", "✷", "✸"]
    glyph = (
        glyph_alphabet[velocity_band]
        + glyph_alphabet[curvature_band]
        + glyph_alphabet[inversion_band]
    )

    signature_seed = f"{label or 'echo'}|{window}|{','.join(f'{v:.4f}' for v in windowed)}"
    signature = sha1(signature_seed.encode()).hexdigest()[:12]

    return ResonanceFingerprint(
        baseline=baseline,
        velocity=velocity,
        curvature=curvature,
        inversion_points=inversions,
        coherence=coherence,
        rarity=rarity,
        glyph=glyph,
        signature=signature,
    )


__all__ = ["ResonanceFingerprint", "compute_resonance_fingerprint"]

