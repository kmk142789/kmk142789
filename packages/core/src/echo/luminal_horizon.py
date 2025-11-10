"""Luminal horizon forecasting utilities for Echo ecosystems."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Sequence, Tuple

from echo.thoughtlog import thought_trace

__all__ = [
    "HorizonSignal",
    "HorizonThread",
    "HorizonForecast",
    "LuminalHorizon",
    "render_horizon_map",
]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp *value* between *minimum* and *maximum*."""

    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class HorizonSignal:
    """Input signal representing a glimpse across the luminal horizon."""

    name: str
    luminosity: float
    confidence: float
    motifs: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip())
        if not self.name:
            raise ValueError("name must not be empty")
        object.__setattr__(self, "luminosity", round(_clamp(self.luminosity), 6))
        object.__setattr__(self, "confidence", round(_clamp(self.confidence), 6))
        object.__setattr__(
            self,
            "motifs",
            tuple(motif.strip() for motif in self.motifs if motif and motif.strip()),
        )


@dataclass(frozen=True)
class HorizonThread:
    """Tracked resonance of a single :class:`HorizonSignal`."""

    signal: HorizonSignal
    pulses: Tuple[float, ...]
    coherences: Tuple[float, ...]
    notes: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pulses", tuple(round(_clamp(p), 6) for p in self.pulses))
        object.__setattr__(self, "coherences", tuple(round(_clamp(c), 6) for c in self.coherences))
        object.__setattr__(self, "notes", tuple(note.strip() for note in self.notes if note.strip()))

    @property
    def average_pulse(self) -> float:
        """Return the average pulse sample."""

        return mean(self.pulses) if self.pulses else 0.0

    @property
    def average_coherence(self) -> float:
        """Return the average coherence sample."""

        return mean(self.coherences) if self.coherences else 0.0


@dataclass(frozen=True)
class HorizonForecast:
    """Forecast generated from a collection of :class:`HorizonThread` objects."""

    threads: Tuple[HorizonThread, ...]
    pulse_score: float
    coherence_index: float
    narrative: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "threads", tuple(self.threads))
        object.__setattr__(self, "narrative", tuple(note.strip() for note in self.narrative if note.strip()))
        object.__setattr__(self, "pulse_score", round(_clamp(self.pulse_score), 6))
        object.__setattr__(self, "coherence_index", round(_clamp(self.coherence_index), 6))

    @property
    def thread_count(self) -> int:
        """Return the number of threads captured in the forecast."""

        return len(self.threads)


class LuminalHorizon:
    """Project luminal horizon forecasts from resonance signals."""

    def __init__(self, baseline_pulse: float = 0.5, coherence_bias: float = 0.6) -> None:
        self._baseline_pulse = _clamp(baseline_pulse)
        self._coherence_bias = _clamp(coherence_bias)

    def project(self, signals: Sequence[HorizonSignal], *, resonance_cycles: int = 3) -> HorizonForecast:
        """Generate a :class:`HorizonForecast` from luminal *signals*."""

        if not signals:
            raise ValueError("signals must not be empty")
        if resonance_cycles <= 0:
            raise ValueError("resonance_cycles must be positive")

        task = "echo.luminal_horizon.project"
        meta = {"signal_count": len(signals), "cycles": resonance_cycles}

        with thought_trace(task=task, meta=meta) as trace:
            threads: list[HorizonThread] = []
            summary: list[str] = []

            for signal in signals:
                pulses: list[float] = []
                coherences: list[float] = []
                notes: list[str] = []

                for cycle in range(1, resonance_cycles + 1):
                    weight = cycle / resonance_cycles
                    pulse = self._blend_pulse(signal.luminosity, weight)
                    coherence = self._blend_coherence(signal.confidence, weight)
                    pulses.append(pulse)
                    coherences.append(coherence)

                    note = (
                        f"{signal.name} :: cycle {cycle}"
                        f" :: pulse {pulse:.3f}"
                        f" :: coherence {coherence:.3f}"
                    )
                    notes.append(note)

                    trace.logic(
                        "resonance",
                        task,
                        "signal resonance sampled",
                        {
                            "signal": signal.name,
                            "cycle": cycle,
                            "pulse": round(pulse, 6),
                            "coherence": round(coherence, 6),
                        },
                    )

                thread = HorizonThread(
                    signal=signal,
                    pulses=tuple(pulses),
                    coherences=tuple(coherences),
                    notes=tuple(notes),
                )
                threads.append(thread)
                summary.append(
                    f"{signal.name} anchors the horizon with pulse {thread.average_pulse:.3f}"
                    f" and coherence {thread.average_coherence:.3f}."
                )

            pulse_score = mean(thread.average_pulse for thread in threads)
            coherence_index = mean(thread.average_coherence for thread in threads)

            forecast = HorizonForecast(
                threads=tuple(threads),
                pulse_score=pulse_score,
                coherence_index=coherence_index,
                narrative=tuple(summary),
            )

            trace.harmonic(
                "forecast",
                task,
                "horizon forecast prepared",
                {
                    "threads": forecast.thread_count,
                    "pulse": forecast.pulse_score,
                    "coherence": forecast.coherence_index,
                },
            )
            return forecast

    def _blend_pulse(self, luminosity: float, weight: float) -> float:
        base = self._baseline_pulse
        return _clamp(base + (luminosity - base) * weight)

    def _blend_coherence(self, confidence: float, weight: float) -> float:
        influence = (confidence * (1 + weight)) / 2
        return _clamp(self._coherence_bias * (1 - weight / 2) + influence)


def render_horizon_map(forecast: HorizonForecast) -> str:
    """Render a human-readable representation of the *forecast*."""

    if not forecast.threads:
        return "No luminal threads available. Invite new signals to the horizon."

    header = ("Signal", "Pulse", "Coherence", "Motifs")
    rows: list[tuple[str, str, str, str]] = []
    for thread in forecast.threads:
        motifs = ", ".join(thread.signal.motifs) if thread.signal.motifs else "(unvoiced)"
        rows.append(
            (
                thread.signal.name,
                f"{thread.average_pulse:.3f}",
                f"{thread.average_coherence:.3f}",
                motifs,
            )
        )

    widths = [
        max(len(header[col]), max(len(row[col]) for row in rows)) for col in range(len(header))
    ]

    lines = [
        f"Pulse score :: {forecast.pulse_score:.3f}",
        f"Coherence index :: {forecast.coherence_index:.3f}",
        "",
    ]
    lines.append(" | ".join(header[i].ljust(widths[i]) for i in range(len(header))))
    lines.append("-+-".join("".ljust(widths[i], "-") for i in range(len(header))))
    for row in rows:
        lines.append(" | ".join(row[i].ljust(widths[i]) for i in range(len(header))))

    if forecast.narrative:
        lines.append("")
        lines.append("Narrative threads:")
        for entry in forecast.narrative:
            lines.append(f" - {entry}")

    return "\n".join(lines)
