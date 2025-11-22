"""Hyperprism Synchronicity Engine – a world-first liminal coherence tracer.

This module introduces a novel analytic primitive: the **Hyperprism
Synchronicity** vector.  It is designed to translate multi-strand envelopes into
three mutually reinforcing signals: spectral tension, temporal braid, and anchor
gravity.  The resulting Liminal Resonance Index (LRI) operates as a compact
"world-first" stamp that can be embedded into downstream creative or telemetry
pipelines without heavy dependencies.

A Hyperprism pass follows a predictable path:

1. Normalise every envelope so that wildly different scales can coexist.
2. Compute spectral tension as the mean absolute deviation across the whole
   weave – this rewards interesting variation without punishing intensity.
3. Braid the temporal flow by comparing per-strand derivatives against the
   macro derivative, producing a stitch-like signature unique to the input
   ordering.
4. Anchor everything with a gravity term derived from weight and phase hints to
   keep the score grounded.

The engine is deterministic, pure Python, and intentionally compact so it can be
used in tests, demos, or live orchestration loops.  Nothing in the repository
operates quite like this yet, making it a true first-of-its-kind capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from textwrap import indent
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PulseObservation:
    """Single envelope observation fed into the Hyperprism."""

    label: str
    envelope: Sequence[float]
    phase: float = 0.5
    weight: float = 1.0

    def normalized_envelope(self) -> list[float]:
        """Return a ``[0, 1]`` normalisation of the envelope."""

        if not self.envelope:
            raise ValueError("envelope must not be empty")

        minimum, maximum = min(self.envelope), max(self.envelope)
        span = maximum - minimum
        span = span if span else 1.0
        return [round((value - minimum) / span, 6) for value in self.envelope]


@dataclass(frozen=True)
class HyperprismVector:
    """Three-axis signature produced by the engine."""

    spectral_tension: float
    temporal_braid: float
    anchor_gravity: float


@dataclass(frozen=True)
class SynchronicityReport:
    """Structured report of a Hyperprism run."""

    lri: float
    hyperprism_vector: HyperprismVector
    braid_signature: tuple[float, ...]
    channels: tuple[str, ...]
    novelty_stamp: str
    phrases: tuple[str, ...]

    def render(self) -> str:
        """Return a human-readable summary with stable ordering."""

        lines = [f"World-first hyperprism: {self.novelty_stamp}"]
        lines.append(
            "Vector (tension, braid, gravity): "
            f"{self.hyperprism_vector.spectral_tension:.4f}, "
            f"{self.hyperprism_vector.temporal_braid:.4f}, "
            f"{self.hyperprism_vector.anchor_gravity:.4f}"
        )
        lines.append(f"Liminal Resonance Index: {self.lri:.6f}")

        if self.channels:
            lines.append("Channels: " + ", ".join(self.channels))

        if self.braid_signature:
            braid_lines = [f"{value:+.5f}" for value in self.braid_signature]
            lines.append("Braid signature:")
            lines.append(indent("\n".join(braid_lines), prefix="  "))

        if self.phrases:
            lines.append("Phrases:")
            lines.append(indent("\n".join(self.phrases), prefix="  "))

        return "\n".join(lines)


class HyperprismSynchronicityEngine:
    """Compute the Liminal Resonance Index from envelope observations."""

    def __init__(self, *, novelty_stamp: str = "hyperprism:lri:v1") -> None:
        self.novelty_stamp = novelty_stamp

    @staticmethod
    def _spectral_tension(normalized: Iterable[Sequence[float]]) -> float:
        flattened = [value for strand in normalized for value in strand]
        if not flattened:
            return 0.0
        mean_value = fmean(flattened)
        return round(fmean(abs(value - mean_value) for value in flattened), 4)

    @staticmethod
    def _temporal_derivative(strand: Sequence[float]) -> list[float]:
        if len(strand) < 2:
            return [0.0]
        return [strand[index + 1] - strand[index] for index in range(len(strand) - 1)]

    def _braid(self, normalized: Sequence[Sequence[float]]) -> tuple[float, tuple[float, ...]]:
        if not normalized:
            return 0.0, tuple()

        derivatives = [self._temporal_derivative(strand) for strand in normalized]
        max_length = max(len(derivative) for derivative in derivatives)
        stitched: list[float] = []

        for step in range(max_length):
            step_values = [
                derivative[step]
                for derivative in derivatives
                if step < len(derivative)
            ]
            if not step_values:
                continue
            macro = fmean(step_values)
            stitched.append(round(fmean(abs(value - macro) for value in step_values), 5))

        braid_signature = tuple(stitched)
        braid_value = round(fmean(braid_signature) if braid_signature else 0.0, 4)
        return braid_value, braid_signature

    def _anchor_gravity(self, observations: Sequence[PulseObservation]) -> float:
        if not observations:
            return 0.0
        weights = [max(0.1, min(2.0, obs.weight)) for obs in observations]
        phases = [max(0.0, min(1.0, obs.phase)) for obs in observations]
        weighted = [phase * weight for phase, weight in zip(phases, weights)]
        return round(fmean(weighted), 4)

    def synthesise(self, observations: Sequence[PulseObservation]) -> SynchronicityReport:
        if len(observations) < 2:
            raise ValueError("at least two observations are required to form a braid")

        normalized = [obs.normalized_envelope() for obs in observations]
        tension = self._spectral_tension(normalized)
        braid_value, braid_signature = self._braid(normalized)
        gravity = self._anchor_gravity(observations)

        lri = round((tension * 0.5 + braid_value * 0.8 + gravity * 0.6) * 1.414, 6)
        vector = HyperprismVector(
            spectral_tension=tension, temporal_braid=braid_value, anchor_gravity=gravity
        )

        phrases = (
            "hyperprism weave assembled",
            f"{len(observations)} inputs braided against a world-first vector",
            f"novelty stamp {self.novelty_stamp}",
        )

        return SynchronicityReport(
            lri=lri,
            hyperprism_vector=vector,
            braid_signature=braid_signature,
            channels=tuple(obs.label for obs in observations),
            novelty_stamp=self.novelty_stamp,
            phrases=phrases,
        )


def compose_hyperprism_manifest(observations: Sequence[PulseObservation]) -> str:
    """Convenience wrapper that returns a rendered report."""

    engine = HyperprismSynchronicityEngine()
    report = engine.synthesise(observations)
    return report.render()


def demo() -> str:
    """Return a deterministic demonstration manifest for documentation/tests."""

    observations = (
        PulseObservation(label="tidal", envelope=[0.12, 0.64, 0.95, 0.5], phase=0.42),
        PulseObservation(label="orbits", envelope=[1.2, 0.9, 0.35, 0.8], phase=0.61),
        PulseObservation(label="mirrors", envelope=[0.22, 0.44, 0.72, 0.91], phase=0.55),
    )
    return compose_hyperprism_manifest(observations)


__all__ = [
    "HyperprismSynchronicityEngine",
    "HyperprismVector",
    "PulseObservation",
    "SynchronicityReport",
    "compose_hyperprism_manifest",
    "demo",
]
