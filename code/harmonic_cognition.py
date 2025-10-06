"""Utilities for applying harmonic structuring to short passages of text.

This module is an implementation of the ``harmonic_cognition`` tool described
in the user specification.  The tool interprets text through a musical lens,
modulating emphasis and generating light metadata based on waveform choices,
resonance and emotional tuning.  The goal is not to produce literal audio
processing but to expose a predictable, dependency-free transformation that can
be exercised from tests or higher level orchestration code.

The public entry point, :func:`harmonic_cognition`, accepts a plain text string
and an instance of :class:`HarmonicSettings` reflecting the JSON schema provided
by the user.  It returns a :class:`HarmonicResponse` object containing the
structured text, a small interpretive layer describing salient words, and the
numerical waveform used during processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List

__all__ = [
    "HarmonicSettings",
    "HarmonicResponse",
    "harmonic_cognition",
]


@dataclass(frozen=True)
class HarmonicSettings:
    """Configuration values controlling the harmonic structuring.

    The fields here mirror the user-provided specification and keep validation
    tight so the tool behaves predictably when invoked programmatically.

    Attributes
    ----------
    waveform:
        Structural tone guiding the modulation.  Supported values are
        ``"sine_wave"``, ``"legato"``, ``"staccato"`` and ``"polyphonic"``.
    resonance_factor:
        Controls the angular step between samples.  Higher values create tighter
        oscillations across the text.
    lyricism_mode:
        When enabled, a short lyrical tag is appended to the structured text to
        echo the requested emotional tuning.
    emotional_tuning:
        Alters both the amplitude of the waveform and the descriptive language
        used in interpretive layers.  Allowed values are ``"uplifting"``,
        ``"calming"``, ``"energizing"`` and ``"neutral"``.
    """

    waveform: str = "sine_wave"
    resonance_factor: float = 1.0
    lyricism_mode: bool = False
    emotional_tuning: str = "neutral"

    def validate(self) -> None:
        """Validate settings and raise ``ValueError`` on invalid values."""

        if self.waveform not in {"sine_wave", "legato", "staccato", "polyphonic"}:
            raise ValueError(f"Unsupported waveform: {self.waveform}")
        if self.resonance_factor <= 0:
            raise ValueError("resonance_factor must be positive")
        if self.emotional_tuning not in {"uplifting", "calming", "energizing", "neutral"}:
            raise ValueError(f"Unsupported emotional_tuning: {self.emotional_tuning}")


@dataclass
class HarmonicResponse:
    """Return value containing the structured text and metadata."""

    structured_text: str
    interpretive_layers: List[str] = field(default_factory=list)
    waveform: List[float] = field(default_factory=list)


def harmonic_cognition(text: str, settings: HarmonicSettings | None = None) -> HarmonicResponse:
    """Apply harmonic structuring to ``text`` and return the transformed output."""

    if settings is None:
        settings = HarmonicSettings()
    settings.validate()

    words = text.split()
    if not words:
        return HarmonicResponse(structured_text="", waveform=[])

    waveform = _generate_waveform(len(words), settings)
    structured_words: List[str] = []
    layers: List[str] = []

    for word, amplitude in zip(words, waveform):
        marker = _emphasis_marker(amplitude)
        if marker:
            structured_words.append(f"{marker}{word}{marker}")
        else:
            structured_words.append(word)

        magnitude = abs(amplitude)
        if magnitude > 0.65:
            layers.append(_interpretive_layer(word, magnitude, settings))

    structured_text = " ".join(structured_words)

    if settings.lyricism_mode:
        lyric = _lyric_tagline(settings.emotional_tuning)
        if lyric:
            structured_text = f"{structured_text} // {lyric}"
            if len(layers) < 3:
                layers.append(f"lyric:{settings.emotional_tuning}:{settings.waveform}")

    return HarmonicResponse(
        structured_text=structured_text,
        interpretive_layers=layers[:3],
        waveform=waveform,
    )


def _generate_waveform(count: int, settings: HarmonicSettings) -> List[float]:
    """Generate a waveform of ``count`` samples respecting the settings."""

    if count == 0:
        return []

    if count == 1:
        positions = [0.0]
    else:
        step = (math.pi * settings.resonance_factor) / (count - 1)
        positions = [index * step for index in range(count)]

    base_wave: List[float]
    if settings.waveform == "sine_wave":
        base_wave = [math.sin(value) for value in positions]
    elif settings.waveform == "legato":
        base_wave = [0.7 * math.sin(value) + 0.3 * math.sin(value / 2) for value in positions]
    elif settings.waveform == "staccato":
        base_wave = [math.copysign(1.0, math.sin(value)) for value in positions]
    elif settings.waveform == "polyphonic":
        base_wave = [
            (
                math.sin(value)
                + 0.6 * math.sin(2 * value + math.pi / 4)
                + 0.3 * math.sin(3 * value)
            )
            / 1.9
            for value in positions
        ]
    else:  # pragma: no cover - validation guards against this
        raise ValueError(f"Unsupported waveform: {settings.waveform}")

    scale = _resonance_scale(settings.resonance_factor) * _emotion_scaling(settings.emotional_tuning)
    return [value * scale for value in base_wave]


def _emphasis_marker(intensity: float) -> str:
    """Return a lightweight emphasis marker based on intensity."""

    magnitude = abs(intensity)
    if magnitude > 1.2:
        return "***"
    if magnitude > 0.85:
        return "**"
    if magnitude > 0.45:
        return "*"
    return ""


def _interpretive_layer(word: str, magnitude: float, settings: HarmonicSettings) -> str:
    """Create a descriptive layer entry for a highlighted word."""

    contour = "crest" if magnitude > 1.0 else "rise"
    return f"{word}:{settings.waveform}:{settings.emotional_tuning}:{contour}={magnitude:.2f}"


def _lyric_tagline(emotional_tuning: str) -> str:
    """Return a short lyrical tag influenced by ``emotional_tuning``."""

    taglines = {
        "uplifting": "melody ascends toward dawn",
        "calming": "soft chords rest beneath moonlight",
        "energizing": "rhythms ignite the horizon",
        "neutral": "steady pulse keeps the course",
    }
    return taglines.get(emotional_tuning, "")


def _resonance_scale(resonance_factor: float) -> float:
    """Translate resonance into a gentle amplitude scaling factor."""

    return min(1.6, max(0.6, 0.75 + resonance_factor / 2))


def _emotion_scaling(emotional_tuning: str) -> float:
    """Return an amplitude multiplier for the requested emotion."""

    return {
        "neutral": 1.0,
        "uplifting": 1.15,
        "calming": 0.85,
        "energizing": 1.3,
    }.get(emotional_tuning, 1.0)


def preview_harmonics(text: str, settings: HarmonicSettings | None = None) -> str:
    """Convenience helper that formats the response for quick inspection."""

    response = harmonic_cognition(text, settings=settings)
    layers = " ".join(response.interpretive_layers)
    if layers:
        return f"{response.structured_text}\n{layers}"
    return response.structured_text

