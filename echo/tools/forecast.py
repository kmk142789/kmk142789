from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Callable, List, Sequence


@dataclass(frozen=True)
class ForecastResult:
    """Represents a blended EMA/AR forecast for amplification indices."""

    history: List[float]
    projections: List[float]
    lower: List[float]
    upper: List[float]
    ema: List[float]


def blended_forecast(values: Sequence[float], steps: int = 3, alpha: float = 0.6) -> ForecastResult:
    """Project future amplification indices using an EMA/AR blend."""

    history = [float(value) for value in values]
    if not history:
        zeros = [0.0 for _ in range(steps)]
        return ForecastResult([], zeros, zeros, zeros, [])

    ema: List[float] = []
    current = history[0]
    for value in history:
        current = alpha * value + (1 - alpha) * current
        ema.append(current)

    window = history[-min(len(history), 5) :]
    if len(window) > 1:
        x_values = list(range(len(window)))
        mean_x = sum(x_values) / len(x_values)
        mean_y = sum(window) / len(window)
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, window))
        denominator = sum((x - mean_x) ** 2 for x in x_values) or 1.0
        slope = numerator / denominator
    else:
        slope = 0.0

    last_ema = ema[-1]
    projections: List[float] = []
    lower: List[float] = []
    upper: List[float] = []
    band_source = history[-min(len(history), 6) :]
    if len(band_source) > 1:
        dispersion = statistics.pstdev(band_source)
    else:
        dispersion = 2.5
    band = max(3.0, dispersion * 1.5)

    for step in range(1, steps + 1):
        ar_component = last_ema + slope * step
        blended = 0.55 * ar_component + 0.45 * last_ema
        blended = max(0.0, min(100.0, blended))
        projections.append(round(blended, 2))
        lower.append(round(max(0.0, blended - band), 2))
        upper.append(round(min(100.0, blended + band), 2))
        last_ema = alpha * blended + (1 - alpha) * last_ema

    return ForecastResult(history, projections, lower, upper, ema)


def render_forecast(
    result: ForecastResult,
    *,
    cycles: Sequence[int],
    last_cycle: int,
    include_plot: bool = False,
    sparkline: Callable[[Sequence[float]], str] | None = None,
) -> str:
    """Render a forecast table and optional ASCII sparkline."""

    lines: List[str] = []
    if result.history:
        recent_cycles = cycles[-len(result.history) :]
        history_summary = ", ".join(
            f"{cycle}:{value:.2f}" for cycle, value in zip(recent_cycles, result.history)
        )
        lines.append(f"History: {history_summary}")
    lines.append("Cycle  Forecast  Lower  Upper")
    for index, value in enumerate(result.projections, start=1):
        cycle = last_cycle + index
        lower = result.lower[index - 1]
        upper = result.upper[index - 1]
        lines.append(f"{cycle:>5}  {value:>8.2f}  {lower:>5.2f}  {upper:>5.2f}")
    if result.projections:
        band = result.upper[0] - result.projections[0]
        lines.append(f"Confidence band ±{band:.2f}")
    if include_plot and sparkline is not None:
        combined = list(result.history) + list(result.projections)
        lines.append(f"Sparkline: {sparkline(combined)}")
    return "\n".join(lines)


__all__ = ["ForecastResult", "blended_forecast", "render_forecast"]
