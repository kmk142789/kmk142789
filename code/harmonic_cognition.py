"""Utilities for applying lightweight harmonic structuring to snippets of text.

The original specification for this module arrived as an extremely dense code
block that relied on ``numpy`` and mixed application logic with console output.
This rewrite keeps the flavour of the original idea—shaping words according to
synthetic wave intensities—while providing a small, dependency-free module that
can be imported from tests or other packages inside the repository.

The public entry point, :func:`harmonic_cognition`, accepts a plain text string
and a :class:`HarmonicSettings` configuration.  It returns a
:class:`HarmonicResponse` object containing the structured text and useful
metadata describing the emphasised words.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable, List

__all__ = [
    "HarmonicSettings",
    "HarmonicResponse",
    "harmonic_cognition",
]


@dataclass(frozen=True)
class HarmonicSettings:
    """Configuration values controlling the harmonic structuring.

    Attributes
    ----------
    waveform:
        Controls the base waveform used to modulate word intensity.  Supported
        values are ``"sine"``, ``"square"``, and ``"complex"``.
    resonance_factor:
        Multiplier applied to the base angular step, stretching or compressing
        the waveform across the text.
    compression:
        When ``True`` the output emphasises individual words using lightweight
        markup (``*`` characters).  When ``False`` the words are repeated to
        reflect their relative intensities.
    symbolic_inflection:
        Optional selector for the glyph set used when inserting separators in
        expanded mode.
    phase_modulation:
        Introduces a linear phase shift across the generated waveform, matching
        the behaviour of the original prototype but without the heavy
        dependency requirements.
    harmonic_scaling:
        Additional multiplier used both when generating the waveform and when
        calculating repetition/emphasis.  Values greater than 1.0 amplify the
        effect of the modulation; values below 1.0 produce a subtler pattern.
    """

    waveform: str = "sine"
    resonance_factor: float = 1.0
    compression: bool = False
    symbolic_inflection: str | None = None
    phase_modulation: bool = False
    harmonic_scaling: float = 1.0

    def validate(self) -> None:
        """Validate settings and raise ``ValueError`` on invalid values."""

        if self.waveform not in {"sine", "square", "complex"}:
            raise ValueError(f"Unsupported waveform: {self.waveform}")
        if self.resonance_factor <= 0:
            raise ValueError("resonance_factor must be positive")
        if self.harmonic_scaling <= 0:
            raise ValueError("harmonic_scaling must be positive")


@dataclass
class HarmonicResponse:
    """Return value containing the structured text and metadata."""

    structured_text: str
    interpretive_layers: List[str] = field(default_factory=list)
    waveform: List[float] = field(default_factory=list)


def harmonic_cognition(text: str, settings: HarmonicSettings | None = None) -> HarmonicResponse:
    """Apply harmonic structuring to ``text``.

    Parameters
    ----------
    text:
        Input text to be processed.  The function operates on whitespace
        separated words to match the behaviour of the historic script.
    settings:
        Optional :class:`HarmonicSettings` instance.  When omitted the defaults
        described in the class docstring are used.
    """

    if settings is None:
        settings = HarmonicSettings()
    settings.validate()

    words = text.split()
    if not words:
        return HarmonicResponse(structured_text="", waveform=[])

    waveform = _generate_waveform(len(words), settings)
    structured_words: List[str] = []
    layers: List[str] = []

    for index, (word, wave_value) in enumerate(zip(words, waveform)):
        intensity = abs(wave_value) * settings.harmonic_scaling
        if settings.phase_modulation:
            intensity *= _semantic_weight(index, len(words))

        if settings.compression:
            emphasis = _emphasis_level(intensity)
            structured_words.append(f"{emphasis}{word}{emphasis}".strip())
            if intensity > 0.7:
                layers.append(f"[{word}:depth={intensity:.2f}]")
        else:
            repetition = max(1, int(intensity * 2) + 1)
            structured_words.extend([word] * repetition)
            if intensity > 0.6:
                structured_words.append(_harmonic_separator(settings.symbolic_inflection, intensity))

    structured_text = " ".join(structured_words).strip()
    return HarmonicResponse(structured_text=structured_text, interpretive_layers=layers[:3], waveform=waveform)


def _generate_waveform(count: int, settings: HarmonicSettings) -> List[float]:
    """Generate a waveform matching ``count`` samples."""

    if count == 1:
        positions = [0.0]
    else:
        step = 2 * math.pi * settings.resonance_factor / (count - 1)
        positions = [index * step for index in range(count)]

    if settings.phase_modulation and count > 1:
        phase_step = (math.pi / 2) / (count - 1)
        positions = [value + index * phase_step for index, value in enumerate(positions)]

    if settings.waveform == "sine":
        return [math.sin(value) * settings.harmonic_scaling for value in positions]
    if settings.waveform == "square":
        return [math.copysign(1.0, math.sin(value)) * settings.harmonic_scaling for value in positions]
    if settings.waveform == "complex":
        return [
            (
                math.sin(value)
                + 0.5 * math.sin(2 * value)
                + 0.25 * math.sin(3 * value)
            )
            / 1.75
            * settings.harmonic_scaling
            for value in positions
        ]
    raise ValueError(f"Unsupported waveform: {settings.waveform}")


def _semantic_weight(index: int, total: int) -> float:
    """Compute an additional phase-based weighting factor."""

    if total <= 1:
        return 1.0
    phase = (index / (total - 1)) * (math.pi / 2)
    return 1 + 0.5 * math.sin(phase)


def _emphasis_level(intensity: float) -> str:
    """Map an intensity value to lightweight emphasis markers."""

    if intensity > 0.8:
        return "***"
    if intensity > 0.5:
        return "**"
    if intensity > 0.2:
        return "*"
    return ""


def _harmonic_separator(inflection: str | None, intensity: float) -> str:
    """Return a glyph separator based on the requested inflection."""

    glyph_sets = {
        "runic": ["ᚱ", "ᚱᚢ", "ᚱᚢᚾ"],
        "hieroglyphic": ["𓂀", "𓂀𓊪", "𓂀𓊪𓏏"],
        "fractal": ["◊", "◊◈", "◊◈◊"],
        None: ["∿", "∿∿", "∿∿∿"],
    }

    level = min(2, int(intensity * 3))
    glyphs = glyph_sets.get(inflection, glyph_sets[None])
    return glyphs[level]


def preview_harmonics(text: str, settings: HarmonicSettings | None = None) -> str:
    """Convenience helper that formats the response for quick inspection."""

    response = harmonic_cognition(text, settings=settings)
    layers = " ".join(response.interpretive_layers)
    if layers:
        return f"{response.structured_text}\n{layers}"
    return response.structured_text

