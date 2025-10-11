"""Cognitive Harmonix text sculpting utilities.

This module implements a light-weight version of the ``cognitive_harmonics``
tool specification that appears in the project documentation.  The intent is
to provide deterministic text transformations that mimic the behaviour of the
schema without requiring external dependencies or network access.  The
``cognitive_harmonix`` function accepts an input passage and a
``CognitiveHarmonixSettings`` instance that mirrors the JSON schema fields.
The function returns a ``CognitiveHarmonixResponse`` object containing the
structured text, glyph overlays, and contextual metadata describing the
transformation that took place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable, List

__all__ = [
    "CognitiveHarmonixSettings",
    "CognitiveHarmonixResponse",
    "cognitive_harmonix",
    "preview_cognitive_harmonix",
]


_SYMBOLIC_TABLE = {
    "runic": ["ᚠ", "ᚢ", "ᚦ", "ᚨ"],
    "hieroglyphic": ["𓂀", "𓆣", "𓃰", "𓇳"],
    "fractal": ["✶", "✹", "✺", "✻"],
    "emoji": ["🌊", "🎵", "✨", "💫"],
}

_EMOTION_TAGS = {
    "uplifting": ("radiant-ascension", "melody ascends toward dawn"),
    "calming": ("lunar-drift", "soft chords rest beneath moonlight"),
    "energizing": ("solar-flare", "rhythms ignite the horizon"),
    "neutral": ("steady-vector", "steady pulse keeps the course"),
}


@dataclass(frozen=True)
class CognitiveHarmonixSettings:
    """Configuration surface that mirrors the published JSON schema."""

    waveform: str = "sine_wave"
    resonance_factor: float = 1.0
    compression: bool = False
    symbolic_inflection: str = "fractal"
    lyricism_mode: bool = False
    emotional_tuning: str = "neutral"

    def validate(self) -> None:
        """Ensure supplied configuration values fall within supported ranges."""

        if self.waveform not in {"sine_wave", "square_wave", "complex_harmonic"}:
            raise ValueError(f"Unsupported waveform: {self.waveform}")
        if self.resonance_factor <= 0:
            raise ValueError("resonance_factor must be positive")
        if self.symbolic_inflection not in _SYMBOLIC_TABLE:
            raise ValueError(
                "Unsupported symbolic_inflection: {0}".format(self.symbolic_inflection)
            )
        if self.emotional_tuning not in _EMOTION_TAGS:
            raise ValueError(f"Unsupported emotional_tuning: {self.emotional_tuning}")


@dataclass
class CognitiveHarmonixResponse:
    """Structured output returned by :func:`cognitive_harmonix`."""

    structured_text: str
    glyph_overlay: str
    emotional_signature: str
    wave_profile: List[float] = field(default_factory=list)
    compression_applied: bool = False


def cognitive_harmonix(
    text: str, settings: CognitiveHarmonixSettings | None = None
) -> CognitiveHarmonixResponse:
    """Apply cognitive harmonic sculpting to ``text`` using ``settings``."""

    if settings is None:
        settings = CognitiveHarmonixSettings()
    settings.validate()

    words = text.split()
    if not words:
        signature = _emotion_signature(settings.emotional_tuning)
        return CognitiveHarmonixResponse(
            structured_text="",
            glyph_overlay="",
            emotional_signature=signature,
            wave_profile=[],
            compression_applied=False,
        )

    wave_profile = _generate_waveform(len(words), settings)
    indexed_wave = list(zip(range(len(words)), words, wave_profile))

    compression_applied = False
    if settings.compression and len(words) > 2:
        compression_applied = True
        retained = _compress_words(indexed_wave)
    else:
        retained = indexed_wave

    structured_words: List[str] = []
    glyphs: List[str] = []
    filtered_profile: List[float] = []

    for _, word, amplitude in retained:
        marker = _intensity_marker(amplitude)
        glyphs.append(_symbolic_glyph(settings.symbolic_inflection, amplitude))
        filtered_profile.append(amplitude)
        structured_words.append(f"{marker}{word}{marker}" if marker else word)

    structured_text = " ".join(structured_words)

    if settings.lyricism_mode:
        lyric = _EMOTION_TAGS[settings.emotional_tuning][1]
        if lyric:
            structured_text = f"{structured_text} // {lyric}"

    signature = _emotion_signature(settings.emotional_tuning)
    glyph_overlay = "".join(glyphs)

    return CognitiveHarmonixResponse(
        structured_text=structured_text,
        glyph_overlay=glyph_overlay,
        emotional_signature=signature,
        wave_profile=filtered_profile,
        compression_applied=compression_applied,
    )


def preview_cognitive_harmonix(
    text: str, settings: CognitiveHarmonixSettings | None = None
) -> str:
    """Convenience helper that formats the response into a single string."""

    response = cognitive_harmonix(text, settings=settings)
    overlay = response.glyph_overlay
    signature = response.emotional_signature
    return f"{response.structured_text}\n{overlay}\n{signature}".strip()


def _generate_waveform(
    count: int, settings: CognitiveHarmonixSettings
) -> List[float]:
    """Generate a waveform profile respecting the requested configuration."""

    if count == 1:
        positions: Iterable[float] = (0.0,)
    else:
        step = (math.pi * settings.resonance_factor) / max(count - 1, 1)
        positions = (index * step for index in range(count))

    if settings.waveform == "sine_wave":
        base_wave = [math.sin(position) for position in positions]
    elif settings.waveform == "square_wave":
        base_wave = [math.copysign(1.0, math.sin(position)) for position in positions]
    elif settings.waveform == "complex_harmonic":
        base_wave = [
            (
                math.sin(position)
                + 0.6 * math.sin(2 * position + math.pi / 6)
                + 0.25 * math.sin(3 * position + math.pi / 3)
            )
            / 1.7
            for position in positions
        ]
    else:  # pragma: no cover - validation guards against this branch
        raise ValueError(f"Unsupported waveform: {settings.waveform}")

    scale = _resonance_scale(settings.resonance_factor)
    emotion_scale = _emotion_scale(settings.emotional_tuning)
    return [value * scale * emotion_scale for value in base_wave]


def _compress_words(indexed_wave: List[tuple[int, str, float]]):
    """Select the most resonant half of ``indexed_wave`` preserving order."""

    limit = max(1, len(indexed_wave) // 2)
    sorted_by_intensity = sorted(
        indexed_wave, key=lambda item: abs(item[2]), reverse=True
    )[:limit]
    keep_indices = {index for index, _, _ in sorted_by_intensity}
    retained = [item for item in indexed_wave if item[0] in keep_indices]
    retained.sort(key=lambda item: item[0])
    return retained


def _intensity_marker(amplitude: float) -> str:
    """Return emphasis markers that correspond to amplitude strength."""

    magnitude = abs(amplitude)
    if magnitude > 1.25:
        return "***"
    if magnitude > 0.95:
        return "**"
    if magnitude > 0.55:
        return "*"
    return ""


def _symbolic_glyph(symbolic_inflection: str, amplitude: float) -> str:
    """Map ``amplitude`` to a glyph drawn from ``symbolic_inflection``."""

    glyphs = _SYMBOLIC_TABLE[symbolic_inflection]
    bucket = min(len(glyphs) - 1, int(abs(amplitude) * len(glyphs)))
    return glyphs[bucket]


def _resonance_scale(resonance_factor: float) -> float:
    """Translate resonance into a friendly amplitude multiplier."""

    return min(1.8, max(0.6, 0.7 + resonance_factor / 1.8))


def _emotion_scale(emotional_tuning: str) -> float:
    """Return an amplitude adjustment derived from emotional tuning."""

    return {
        "neutral": 1.0,
        "uplifting": 1.12,
        "calming": 0.88,
        "energizing": 1.28,
    }.get(emotional_tuning, 1.0)


def _emotion_signature(emotional_tuning: str) -> str:
    """Return a descriptive signature string for the requested emotion."""

    tag, _ = _EMOTION_TAGS[emotional_tuning]
    return f"{emotional_tuning}:{tag}"

