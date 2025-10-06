"""Utilities for sculpting text into sine-inspired wave patterns."""

from __future__ import annotations

import math
from typing import Iterable, List

__all__ = ["sine_wave_text"]


def _generate_wave(samples: int, *, frequency: float, amplitude: float) -> List[float]:
    """Return ``samples`` equally spaced sine values for the given parameters."""

    if samples <= 0:
        return []

    if samples == 1:
        return [math.sin(0.0) * amplitude]

    span = math.pi * frequency
    step = span / (samples - 1)
    return [math.sin(index * step) * amplitude for index in range(samples)]


def sine_wave_text(
    text: str,
    *,
    frequency: float = 1.5,
    amplitude: float = 2.0,
    divider: str = "|",
) -> str:
    """Arrange ``text`` so that words repeat following a sine wave envelope.

    Parameters
    ----------
    text:
        The input passage that will be transformed.
    frequency:
        The number of oscillations to perform across the full text.
    amplitude:
        Controls the strength of the wave.  Larger values cause more word
        repetition.  The absolute value is rounded to the nearest integer and
        clamped so that each word appears at least once.
    divider:
        A short token inserted between wave peaks to improve readability.  Set
        to an empty string to disable separators.

    Returns
    -------
    str
        The transformed text.
    """

    words = text.split()
    if not words:
        return ""

    wave = _generate_wave(len(words), frequency=frequency, amplitude=amplitude)

    parts: List[str] = []
    for word, value in zip(words, wave):
        intensity = max(1, math.floor(abs(value)) + 1)
        parts.append(" ".join([word] * intensity))
        if intensity > 1 and divider:
            parts.append(divider)

    if divider and parts and parts[-1] == divider:
        parts.pop()

    return " ".join(parts)

