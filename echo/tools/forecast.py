"""Forecast utilities for amplification indices."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class ForecastResult:
    """Combined AR/EMA projection for upcoming amplification indices."""

    history: List[float]
    ema: List[float]
    projection: List[float]
    confidence: float


def _ema_series(values: Sequence[float], alpha: float) -> List[float]:
    if not values:
        return []
    ema: List[float] = [float(values[0])]
    for value in values[1:]:
        ema.append(alpha * float(value) + (1 - alpha) * ema[-1])
    return ema


def blend_forecast(history: Sequence[float], *, horizon: int = 3, alpha: float = 0.6) -> ForecastResult:
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    values = list(history)
    ema = _ema_series(values, alpha)
    if len(values) >= 2:
        trend = values[-1] - values[-2]
    else:
        trend = 0.0
    last_value = values[-1] if values else 0.0
    ema_tail = ema[-1] if ema else last_value
    projection: List[float] = []
    for step in range(1, horizon + 1):
        ar_estimate = last_value + trend * step
        ema_future = alpha * ar_estimate + (1 - alpha) * ema_tail
        blended = (ar_estimate + ema_future) / 2.0
        projection.append(round(blended, 2))
        ema_tail = ema_future
    sample = values[-min(len(values), max(2, horizon * 2)) :]
    if len(sample) > 1:
        variance = statistics.pvariance(sample)
    else:
        variance = 1.0
    confidence = round(max(1.5, math.sqrt(variance) * 1.1), 2)
    return ForecastResult(history=values, ema=ema, projection=projection, confidence=confidence)


def format_forecast_table(result: ForecastResult) -> str:
    lines: List[str] = []
    lines.append("Step  Actual  EMA    Forecast  +/-")
    lines.append("----  ------  -----  --------  ----")
    if not result.history:
        lines.append(" (no historical data)")
    for index, value in enumerate(result.history):
        label = "t0" if index == len(result.history) - 1 else f"t-{len(result.history) - index - 1}"
        ema_value = result.ema[index] if index < len(result.ema) else result.ema[-1] if result.ema else 0.0
        lines.append(f"{label:>4}  {value:6.2f}  {ema_value:6.2f}     --     --")
    for step, forecast in enumerate(result.projection, start=1):
        lines.append(f"+{step:>3}     --     --  {forecast:8.2f}  ±{result.confidence:.2f}")
    return "\n".join(lines)


_BARS = "▁▂▃▄▅▆▇█"


def ascii_sparkline(values: Sequence[float]) -> str:
    if not values:
        return "No projection available."
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        spark = _BARS[-1] * len(values)
    else:
        scale = (len(_BARS) - 1) / (hi - lo)
        spark = "".join(
            _BARS[int(round((value - lo) * scale))] for value in values
        )
    return f"Forecast: {spark}  ({lo:.1f}→{hi:.1f})"


__all__ = ["ForecastResult", "blend_forecast", "format_forecast_table", "ascii_sparkline"]
