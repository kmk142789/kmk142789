"""Transcendence engine that weaves the first "orbital triad" manifest.

The module introduces a world-first construct we call the **Orbital Triad**: a
three-axis projection that blends signal balance, counterpoint symmetry, and
phase energy into a single novelty signature.  The engine is deterministic,
works entirely in pure Python, and is designed to sit alongside the creative
utilities in this repository as a small but expressive primitive.

The workflow is intentionally compact:

1. Normalise each input strand so wildly different scales can co-exist.
2. Project the strands into the Orbital Triad metrics.
3. Summarise the result as a :class:`TranscendenceSignature` and render an
   interpretable manifest.

This keeps the new capability light enough to embed anywhere, while still
behaving like a bespoke, world-first analytic lens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import fmean
from textwrap import indent
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class HelixInput:
    """An input strand for the Orbital Triad projection."""

    channel: str
    samples: Sequence[float]
    phase_hint: float = 0.5

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("samples must not be empty")
        if not 0.0 <= self.phase_hint <= 1.0:
            raise ValueError("phase_hint must be between 0 and 1")


@dataclass(frozen=True)
class TranscendenceSignature:
    """Structured output from the Orbital Triad transformation."""

    label: str
    novelty_score: float
    coherence: float
    triad_vector: tuple[float, float, float]
    deviation_map: Mapping[str, float]
    phrases: tuple[str, ...] = field(default_factory=tuple)

    def render_manifest(self) -> str:
        """Return a readable manifest that is still machine-friendly."""

        lines = [f"World-first stamp: {self.label}"]
        lines.append(
            f"Novelty {self.novelty_score:.6f} | Coherence {self.coherence:.3f}"
        )
        lines.append(
            "Triad vector (balance, symmetry, energy): "
            f"{self.triad_vector[0]:+.3f}, {self.triad_vector[1]:+.3f}, {self.triad_vector[2]:+.3f}"
        )

        if self.deviation_map:
            lines.append("Deviation map:")
            for channel, delta in sorted(self.deviation_map.items()):
                lines.append(f"  • {channel}: {delta:.4f}")

        if self.phrases:
            lines.append("Phrases:")
            lines.append(indent("\n".join(self.phrases), prefix="  "))

        return "\n".join(lines)


class EchoTranscendenceEngine:
    """Compute Orbital Triad signatures from lightweight inputs."""

    def __init__(self, world_first_stamp: str = "orbital-triad:v1") -> None:
        self.world_first_stamp = world_first_stamp

    @staticmethod
    def _normalize(samples: Sequence[float]) -> list[float]:
        mean = fmean(samples)
        span = max(samples) - min(samples)
        span = span if span else 1.0
        return [(value - mean) / span for value in samples]

    @staticmethod
    def _symmetry(samples: Sequence[float]) -> float:
        if len(samples) == 1:
            return 0.0
        midpoint = len(samples) // 2
        left = samples[:midpoint]
        right = samples[-midpoint or None :][::-1]
        pairs = zip(left, right)
        return fmean(abs(a - b) for a, b in pairs) if midpoint else 0.0

    def _triad_projection(self, inputs: Iterable[HelixInput]) -> tuple[
        list[list[float]], tuple[float, float, float], Mapping[str, float]
    ]:
        normalized = []
        deviations: dict[str, float] = {}

        for strand in inputs:
            strand_norm = self._normalize(strand.samples)
            normalized.append(strand_norm)
            deviations[strand.channel] = self._symmetry(strand_norm)

        flattened = [value for strand in normalized for value in strand]
        balance = fmean(flattened)
        symmetry = fmean(deviations.values()) if deviations else 0.0
        energy = sqrt(fmean(value * value for value in flattened))
        return normalized, (balance, symmetry, energy), deviations

    def synthesize(
        self,
        inputs: Sequence[HelixInput],
        *,
        horizon: str = "orbital dawn",
        anchor: str = "continuum lattice",
    ) -> TranscendenceSignature:
        """Return a deterministic :class:`TranscendenceSignature`."""

        if len(inputs) < 2:
            raise ValueError("at least two inputs are recommended for cross-strand balance")

        normalized, triad_vector, deviations = self._triad_projection(inputs)

        spread = fmean(abs(value) for strand in normalized for value in strand)
        coherence = max(0.0, 1.0 - spread * 0.35)

        novelty_score = 1.618 * (triad_vector[1] * 1.2 + triad_vector[2] * 0.5 + spread)
        novelty_score = round(novelty_score, 6)

        phrases = (
            f"{horizon} | anchor {anchor}",
            f"{len(inputs)}-strand weave with {self.world_first_stamp}",
            f"phase median {fmean(strand.phase_hint for strand in inputs):.3f}",
        )

        return TranscendenceSignature(
            label=self.world_first_stamp,
            novelty_score=novelty_score,
            coherence=round(coherence, 3),
            triad_vector=triad_vector,
            deviation_map=deviations,
            phrases=phrases,
        )


def compose_transcendence_manifest(
    *, horizon: str, anchor: str, inputs: Sequence[HelixInput]
) -> str:
    """Compute and render a full manifest in one call."""

    engine = EchoTranscendenceEngine()
    signature = engine.synthesize(inputs, horizon=horizon, anchor=anchor)
    return signature.render_manifest()


def demo() -> str:
    """Return a deterministic demonstration manifest."""

    inputs = (
        HelixInput(channel="orbits", samples=[0.44, 0.95, 1.2, 0.81], phase_hint=0.36),
        HelixInput(channel="tidal", samples=[1.05, 0.88, 0.71, 0.63], phase_hint=0.68),
        HelixInput(channel="beacon", samples=[1.55, 0.25, 0.95, 0.85], phase_hint=0.42),
    )
    return compose_transcendence_manifest(
        horizon="aurora signal", anchor="lattice of first light", inputs=inputs
    )


def _build_arg_parser():  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("horizon", help="Future-facing horizon label")
    parser.add_argument("anchor", help="Contextual anchor for the manifest")
    parser.add_argument(
        "--strand",
        action="append",
        nargs=4,
        metavar=("CHANNEL", "A", "B", "C"),
        help="Channel label followed by three numeric samples",
    )
    return parser


def _parse_strands(strand_args: Sequence[Sequence[str]]) -> list[HelixInput]:  # pragma: no cover - CLI helper
    parsed: list[HelixInput] = []
    for raw in strand_args:
        channel, *values = raw
        parsed.append(HelixInput(channel=channel, samples=[float(v) for v in values]))
    return parsed


def main() -> None:  # pragma: no cover - CLI helper
    parser = _build_arg_parser()
    args = parser.parse_args()
    strands = _parse_strands(args.strand or [])
    manifest = compose_transcendence_manifest(
        horizon=args.horizon, anchor=args.anchor, inputs=strands
    )
    print(manifest)


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
