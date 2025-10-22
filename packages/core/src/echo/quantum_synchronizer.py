"""Quantum synchronizer for harmonics-driven resonance orchestration.

The synchronizer stitches together :mod:`echo.resonance` primitives into a
higher-level analytical engine.  It collects harmonic responses, computes
stability metrics, and produces a manifest describing how the signal surface is
shifting in near real time.  The module is intentionally deterministic when an
explicit :class:`random.Random` instance is supplied to the underlying
:class:`~echo.resonance.HarmonicsAI`, making it friendly for both testing and
interactive exploration.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, List, Optional

import math
import time

from .resonance import HarmonicsAI


@dataclass(slots=True)
class SynchronizerSignal:
    """Snapshot of a single harmonic observation ingested by the synchronizer."""

    text: str
    harmonic_score: float
    pattern: Optional[str]
    timestamp: float
    weight: float
    message: str


@dataclass(slots=True)
class SynchronizerReport:
    """Computed metrics summarizing the current synchronizer horizon."""

    weighted_score: float = 0.0
    resonance_drift: float = 0.0
    stability_index: float = 0.0
    pattern_diversity: float = 0.0
    momentum: float = 0.0
    novelty_burst: float = 0.0

    def as_dict(self) -> dict:
        """Return the report as a plain dictionary for serialization."""

        return {
            "weighted_score": self.weighted_score,
            "resonance_drift": self.resonance_drift,
            "stability_index": self.stability_index,
            "pattern_diversity": self.pattern_diversity,
            "momentum": self.momentum,
            "novelty_burst": self.novelty_burst,
        }


class QuantumSynchronizer:
    """Fuse harmonic responses into an interpretable, future-facing signal."""

    def __init__(
        self,
        harmonics: Optional[HarmonicsAI] = None,
        *,
        horizon: int = 24,
        drift_window: int = 6,
    ) -> None:
        if horizon < 1:
            raise ValueError("horizon must be positive")
        if drift_window < 2:
            raise ValueError("drift_window must be at least 2")

        self.harmonics = harmonics or HarmonicsAI()
        self.horizon = horizon
        self.drift_window = drift_window
        self._signals: Deque[SynchronizerSignal] = deque()
        self._pattern_counts: Counter[str] = Counter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ingest(
        self,
        text: str,
        *,
        weight: float = 1.0,
        timestamp: Optional[float] = None,
    ) -> SynchronizerSignal:
        """Feed ``text`` into the synchronizer and return the resulting signal."""

        response = self.harmonics.respond(text)
        ts = time.time() if timestamp is None else timestamp
        signal = SynchronizerSignal(
            text=text,
            harmonic_score=response.harmonic_score,
            pattern=response.pattern,
            timestamp=ts,
            weight=max(0.0, float(weight)),
            message=response.message,
        )
        self._append_signal(signal)
        return signal

    def synchronize(self) -> SynchronizerReport:
        """Return the current system metrics across the observed horizon."""

        if not self._signals:
            return SynchronizerReport()

        scores = [signal.harmonic_score for signal in self._signals]
        weights = [signal.weight for signal in self._signals]
        total_weight = sum(weights)

        if total_weight <= 0.0:
            weighted_score = sum(scores) / float(len(scores))
        else:
            weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight

        if len(scores) > 1:
            resonance_drift = scores[-1] - scores[0]
            transitions = [abs(curr - prev) for prev, curr in zip(scores, scores[1:])]
            avg_transition = sum(transitions) / float(len(transitions))
            stability_index = 1.0 / (1.0 + avg_transition)
        else:
            resonance_drift = 0.0
            stability_index = 1.0

        pattern_observations = sum(self._pattern_counts.values())
        if pattern_observations:
            pattern_diversity = len(self._pattern_counts) / float(pattern_observations)
        else:
            pattern_diversity = 0.0

        momentum = self._compute_momentum()
        novelty_burst = self._compute_novelty()

        return SynchronizerReport(
            weighted_score=weighted_score,
            resonance_drift=resonance_drift,
            stability_index=stability_index,
            pattern_diversity=pattern_diversity,
            momentum=momentum,
            novelty_burst=novelty_burst,
        )

    def emergent_manifest(self) -> str:
        """Render a descriptive summary of the latest synchronizer state."""

        report = self.synchronize()
        lines = [
            "Quantum Synchronizer Manifest",
            f"Signals tracked: {len(self._signals)}",
            f"Weighted score: {report.weighted_score:.3f}",
            f"Resonance drift: {report.resonance_drift:.3f}",
            f"Stability index: {report.stability_index:.3f}",
            f"Pattern diversity: {report.pattern_diversity:.3f}",
            f"Momentum: {report.momentum:.3f}",
            f"Novelty burst: {report.novelty_burst:.3f}",
        ]
        if self._signals:
            lines.append(f"Last signal: {self._signals[-1].message}")
        return "\n".join(lines)

    def history(self) -> List[SynchronizerSignal]:
        """Return a copy of the synchronizer history."""

        return list(self._signals)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_signal(self, signal: SynchronizerSignal) -> None:
        if len(self._signals) >= self.horizon:
            oldest = self._signals.popleft()
            if oldest.pattern is not None:
                count = self._pattern_counts.get(oldest.pattern, 0) - 1
                if count <= 0:
                    self._pattern_counts.pop(oldest.pattern, None)
                else:
                    self._pattern_counts[oldest.pattern] = count
        self._signals.append(signal)
        if signal.pattern is not None:
            self._pattern_counts[signal.pattern] += 1

    def _compute_momentum(self) -> float:
        history = self.harmonics.score_history
        if len(history) < 2:
            return 0.0
        window = min(self.drift_window, len(history))
        if window < 2:
            return 0.0
        return self.harmonics.resonance_trend(window)

    def _compute_novelty(self) -> float:
        if not self._signals:
            return 0.0
        latest = self._signals[-1]
        if latest.pattern is None:
            return 0.0
        count = self._pattern_counts.get(latest.pattern, 0)
        if count <= 1:
            return 1.0
        # Penalize frequently recurring patterns while keeping result in (0, 1].
        return 1.0 / math.log2(count + 1.0)


__all__ = ["QuantumSynchronizer", "SynchronizerSignal", "SynchronizerReport"]
