"""Momentum analytics for Continuum manifests.

The existing :mod:`echo.continuum_engine` module focuses on deterministic
recording and replay of continuum breadcrumbs.  Downstream dashboards often
want to highlight which tags or sources are gaining or losing emphasis across
recent entries.  This module provides a light-weight analytic layer that can
be applied to any :class:`~echo.continuum_engine.ContinuumManifest` without
requiring bespoke aggregation logic in each consumer.

Two helper functions—:func:`compute_tag_momentum` and
:func:`compute_source_momentum`—calculate rolling averages across the
chronological manifest entries and describe whether the subject is rising,
falling, or holding steady within the chosen window.  The computations are
pure, deterministic, and return small dataclasses that are easy to surface in
reports or tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

from .continuum_engine import ContinuumManifest

__all__ = [
    "MomentumInsight",
    "compute_tag_momentum",
    "compute_source_momentum",
]


@dataclass(frozen=True, slots=True)
class MomentumInsight:
    """Describe the momentum of a Continuum subject.

    Attributes
    ----------
    subject:
        Name of the tag or source the insight refers to.
    momentum:
        Difference between the trailing and leading window averages.  Positive
        values indicate increasing emphasis, negative values indicate decline.
    latest_weight:
        Weight of the most recent occurrence of ``subject``.
    trend:
        Human-friendly label describing the direction.  One of ``"rising"``,
        ``"falling"``, or ``"steady"``.
    """

    subject: str
    momentum: float
    latest_weight: float
    trend: str

    def render_summary(self) -> str:
        """Return a compact textual summary of the insight."""

        direction_symbol = {
            "rising": "↑",
            "falling": "↓",
            "steady": "→",
        }.get(self.trend, "→")
        return (
            f"{self.subject}: {direction_symbol} {self.trend} "
            f"(latest {self.latest_weight:.2f}, Δ{self.momentum:+.2f})"
        )


def compute_tag_momentum(
    manifest: ContinuumManifest,
    *,
    window: int = 3,
    tolerance: float = 0.05,
) -> Sequence[MomentumInsight]:
    """Return momentum insights for tags referenced in ``manifest``.

    Parameters
    ----------
    manifest:
        Continuum manifest to analyse.
    window:
        Number of entries considered for the leading and trailing averages.
        The value must be at least one; smaller manifests automatically use the
        available number of observations.
    tolerance:
        Minimum absolute momentum required before an insight is considered
        ``"rising"`` or ``"falling"``.  Smaller deltas are labelled ``"steady"``
        to avoid noisy oscillations.
    """

    sequences = _collect_tag_sequences(manifest.entries)
    return _summarise_sequences(sequences, window=window, tolerance=tolerance)


def compute_source_momentum(
    manifest: ContinuumManifest,
    *,
    window: int = 3,
    tolerance: float = 0.05,
) -> Sequence[MomentumInsight]:
    """Return momentum insights for sources referenced in ``manifest``."""

    sequences = _collect_source_sequences(manifest.entries)
    return _summarise_sequences(sequences, window=window, tolerance=tolerance)


def _collect_tag_sequences(entries: Sequence[Mapping[str, object]]) -> Dict[str, List[float]]:
    sequences: Dict[str, List[float]] = {}
    for payload in entries:
        weight = float(payload.get("weight", 0.0))
        for tag in payload.get("tags", []) or ():
            sequences.setdefault(str(tag), []).append(weight)
    return sequences


def _collect_source_sequences(entries: Sequence[Mapping[str, object]]) -> Dict[str, List[float]]:
    sequences: Dict[str, List[float]] = {}
    for payload in entries:
        weight = float(payload.get("weight", 0.0))
        source = str(payload.get("source", ""))
        if source:
            sequences.setdefault(source, []).append(weight)
    return sequences


def _summarise_sequences(
    sequences: Mapping[str, Sequence[float]],
    *,
    window: int,
    tolerance: float,
) -> Sequence[MomentumInsight]:
    if window <= 0:
        raise ValueError("window must be at least 1")
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")

    insights: List[MomentumInsight] = []
    for subject, weights in sequences.items():
        if not weights:
            continue
        momentum, latest_weight = _momentum(weights, window)
        trend = _classify(momentum, tolerance)
        insights.append(
            MomentumInsight(
                subject=subject,
                momentum=momentum,
                latest_weight=latest_weight,
                trend=trend,
            )
        )

    insights.sort(
        key=lambda item: (abs(item.momentum), item.subject.lower()),
        reverse=True,
    )
    return tuple(insights)


def _momentum(weights: Sequence[float], window: int) -> Tuple[float, float]:
    window_size = min(window, len(weights))
    leading_avg = _average(weights[:window_size])
    trailing_avg = _average(weights[-window_size:])
    momentum = trailing_avg - leading_avg
    latest_weight = float(weights[-1])
    return momentum, latest_weight


def _average(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _classify(momentum: float, tolerance: float) -> str:
    if momentum > tolerance:
        return "rising"
    if momentum < -tolerance:
        return "falling"
    return "steady"
