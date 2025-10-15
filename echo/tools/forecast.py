"""Forecast utilities for projecting amplification index trends."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable, List, Sequence


BLOCKS = "▁▂▃▄▅▆▇█"


@dataclass(frozen=True)
class ForecastPoint:
    step: int
    value: float
    lower: float
    upper: float


@dataclass(frozen=True)
class ForecastResult:
    history: List[float]
    projections: List[ForecastPoint]
    alpha: float
    ar_weight: float
    volatility: float


def _ema(values: Sequence[float], alpha: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ema = values[0]
    for value in values[1:]:
        ema = alpha * value + (1.0 - alpha) * ema
    return ema


def blended_forecast(
    history: Sequence[float],
    *,
    horizon: int = 3,
    alpha: float = 0.6,
    ar_weight: float = 0.55,
) -> ForecastResult:
    """Project ``horizon`` future values using an AR/EMA blend."""

    if horizon < 1:
        raise ValueError("horizon must be positive")
    if not history:
        raise ValueError("history must contain at least one value")

    ema_base = _ema(history, alpha)
    last = history[-1]
    if len(history) >= 2:
        deltas = [history[i] - history[i - 1] for i in range(1, len(history))]
        drift = mean(deltas)
        volatility = pstdev(deltas) if len(deltas) > 1 else abs(drift)
    else:
        drift = 0.0
        volatility = 5.0

    projections: List[ForecastPoint] = []
    ema_value = ema_base
    reference = last
    for step in range(1, horizon + 1):
        ema_value = alpha * reference + (1.0 - alpha) * ema_value
        reference = reference + drift
        blended = ar_weight * reference + (1.0 - ar_weight) * ema_value
        confidence = max(volatility * math.sqrt(step), 3.0)
        projections.append(
            ForecastPoint(
                step=step,
                value=round(blended, 2),
                lower=round(max(0.0, blended - confidence), 2),
                upper=round(min(100.0, blended + confidence), 2),
            )
        )

    return ForecastResult(
        history=list(history),
        projections=projections,
        alpha=alpha,
        ar_weight=ar_weight,
        volatility=round(volatility, 4),
    )


def render_table(result: ForecastResult) -> str:
    headers = ["Step", "Projection", "Band"]
    rows = [headers, ["-", "-", "-"]]
    for point in result.projections:
        rows.append(
            [
                str(point.step),
                f"{point.value:.2f}",
                f"{point.lower:.2f} – {point.upper:.2f}",
            ]
        )

    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    lines = []
    for row in rows:
        lines.append(
            " ".join(value.rjust(width) for value, width in zip(row, widths))
        )
    return "\n".join(lines)


def ascii_sparkline(values: Iterable[float]) -> str:
    values = list(values)
    if not values:
        return ""
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        index = len(BLOCKS) // 2
        return BLOCKS[index] * len(values)
    span = high - low
    chars = []
    for value in values:
        normalised = (value - low) / span
        index = min(len(BLOCKS) - 1, int(round(normalised * (len(BLOCKS) - 1))))
        chars.append(BLOCKS[index])
    return "".join(chars)


__all__ = [
    "ForecastPoint",
    "ForecastResult",
    "blended_forecast",
    "render_table",
    "ascii_sparkline",
]

