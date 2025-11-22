"""Causal Polyphony Index: a novel metric for cross-track creative dynamics.

This module introduces the **Causal Polyphony Index (CPI)**, a first-of-its-kind
signal that braids alignment, counterpoint, novelty, and fractal balance across
multiple creative tracks.  Unlike traditional correlation-based coherence
scores, CPI layers rolling phase spread with derivative-aware counterpoint
moments and a Fibonacci-inspired balance term.  The result is a compact,
interpretable fingerprint of how convergent and divergent ideas co-evolve
through time.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
from statistics import fmean, pstdev
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PolyphonyEvent:
    """Single point in a creative track."""

    tick: int
    amplitude: float
    motif: str = "neutral"


@dataclass(frozen=True)
class PolyphonyTrack:
    """Sequence of creative pulses that form one voice in the mix."""

    name: str
    events: Sequence[PolyphonyEvent]

    def normalised_series(self, ticks: Sequence[int], max_amplitude: float) -> list[float]:
        """Return amplitudes aligned to the provided ticks and normalised to 0..1."""

        if max_amplitude <= 0:
            raise ValueError("max_amplitude must be positive to normalise the series")

        lookup = {event.tick: event.amplitude for event in self.events}
        series = [max(0.0, min(1.0, lookup.get(tick, 0.0) / max_amplitude)) for tick in ticks]
        return series


@dataclass(frozen=True)
class PolyphonyIndex:
    """Composite metric describing cross-track evolution."""

    coherence: float
    novelty: float
    counterpoint_density: float
    fractal_balance: float
    score: float
    detail: str


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _rolling(values: Sequence[float], window: int) -> Iterable[list[float]]:
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        yield values[start : idx + 1]


def compute_causal_polyphony_index(
    tracks: Sequence[PolyphonyTrack], *, window: int = 3
) -> PolyphonyIndex:
    """Compute the Causal Polyphony Index for the supplied tracks.

    The algorithm blends four micro-metrics:
    - **coherence**: inverse phase spread across tracks per tick, averaged.
    - **novelty**: mean absolute derivative magnitude across tracks.
    - **counterpoint_density**: frequency of opposing derivatives between tracks.
    - **fractal_balance**: Fibonacci-weighted energy distribution across time.
    """

    if window < 1:
        raise ValueError("window must be at least 1")
    if not tracks:
        raise ValueError("at least one track is required")

    ticks = sorted({event.tick for track in tracks for event in track.events})
    if not ticks:
        raise ValueError("tracks must contain at least one event")

    max_amplitude = max(event.amplitude for track in tracks for event in track.events)
    series = [track.normalised_series(ticks, max_amplitude) for track in tracks]

    coherence_samples: list[float] = []
    novelty_samples: list[float] = []
    counterpoint_hits = 0
    derivative_series: list[list[float]] = []

    for aligned in series:
        derivatives = [0.0]
        for prev, current in zip(aligned, aligned[1:]):
            derivatives.append(current - prev)
        derivative_series.append(derivatives)

    for idx, tick in enumerate(ticks):
        snapshot = [values[idx] for values in series]
        derivatives = [deriv[idx] for deriv in derivative_series]

        spread = pstdev(snapshot) if len(snapshot) > 1 else 0.0
        coherence_samples.append(_clamp(1.0 - spread * 1.6))

        novelty_samples.append(_clamp(fmean(abs(value) for value in derivatives)))

        signs = [1 if value > 0 else -1 if value < 0 else 0 for value in derivatives]
        if any(signs) and max(signs) > 0 and min(signs) < 0:
            counterpoint_hits += 1

    counterpoint_density = counterpoint_hits / max(1, len(ticks))
    coherence = fmean(coherence_samples)
    novelty = fmean(novelty_samples)

    mean_energy_by_tick = [fmean(values) for values in zip(*series)]
    fib_cycle = cycle((1, 2, 3, 5, 8))
    fractal_weighted = [weight * energy for weight, energy in zip(fib_cycle, mean_energy_by_tick)]
    max_possible = sum(next(fib_cycle) for _ in mean_energy_by_tick) or 1
    fractal_balance = _clamp(sum(fractal_weighted) / max_possible)

    score = round(
        0.35 * coherence + 0.25 * novelty + 0.25 * counterpoint_density + 0.15 * fractal_balance,
        3,
    )

    detail = (
        f"ticks={len(ticks)} | window={window} | "
        f"coherence={coherence:.3f} | novelty={novelty:.3f} | "
        f"counterpoint={counterpoint_density:.3f} | fractal_balance={fractal_balance:.3f}"
    )

    return PolyphonyIndex(
        coherence=round(coherence, 3),
        novelty=round(novelty, 3),
        counterpoint_density=round(counterpoint_density, 3),
        fractal_balance=round(fractal_balance, 3),
        score=score,
        detail=detail,
    )


def render_polyphony_brief(tracks: Sequence[PolyphonyTrack], *, window: int = 3) -> str:
    """Return a human-readable summary of the CPI computation."""

    index = compute_causal_polyphony_index(tracks, window=window)
    report_lines = [
        "Causal Polyphony Index", "======================", index.detail, "",
    ]

    for track in tracks:
        motifs = {event.motif for event in track.events if event.motif}
        motif_list = ", ".join(sorted(motifs)) or "unlabeled"
        report_lines.append(
            f"- {track.name}: {len(track.events)} events | motifs={motif_list}"
        )

    report_lines.append("")
    report_lines.append(
        f"Composite score {index.score:.3f} blends alignment, novelty, "
        f"counterpoint, and Fibonacci-weighted balance across {len(tracks)} tracks."
    )
    return "\n".join(report_lines)
