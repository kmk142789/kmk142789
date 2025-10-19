"""Amplification index forecasting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class ForecastResult:
    baseline: float
    projections: List[float]
    confidence_band: float


def _ema(values: Sequence[float], alpha: float = 0.45) -> float:
    if not values:
        return 0.0
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1 - alpha) * result
    return result


def _trend(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    deltas = [b - a for a, b in zip(values[:-1], values[1:])]
    return sum(deltas) / len(deltas)


def _stddev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def project_indices(values: Sequence[float], *, horizon: int = 3) -> ForecastResult:
    if not values:
        return ForecastResult(0.0, [0.0] * horizon, 0.0)

    baseline = values[-1]
    ema_value = _ema(values)
    trend = _trend(values)
    projections: List[float] = []
    for step in range(1, horizon + 1):
        ar_component = baseline + trend * step
        blended = 0.6 * ar_component + 0.4 * ema_value
        projections.append(round(max(0.0, min(100.0, blended)), 2))

    band = round(_stddev(values[-min(len(values), 6):]) * 1.15, 2)
    return ForecastResult(round(baseline, 2), projections, band)


def sparkline(values: Iterable[float], *, width: int = 20) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    series = list(values)
    if not series:
        return ""
    if len(series) > width:
        step = len(series) / width
        condensed = []
        index = 0.0
        while len(condensed) < width and int(index) < len(series):
            condensed.append(series[int(index)])
            index += step
        series = condensed
    minimum = min(series)
    maximum = max(series)
    span = maximum - minimum or 1.0
    chars = []
    for value in series:
        normalized = (value - minimum) / span
        bucket = min(len(blocks) - 1, int(round(normalized * (len(blocks) - 1))))
        chars.append(blocks[bucket])
    return "".join(chars)


__all__ = ["ForecastResult", "project_indices", "sparkline"]

