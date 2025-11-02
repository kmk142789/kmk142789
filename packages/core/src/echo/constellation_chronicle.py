"""Chronicles for multi-phase constellation narratives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, List, Sequence, Tuple

from echo.constellation_weaver import (
    ConstellationWeave,
    ConstellationWeaverError,
    generate_constellation_weave,
)


_ACCENT_PALETTE: Tuple[str, ...] = (
    "luminal cadence",
    "resonant drift",
    "glistening chord",
    "celestial trace",
    "mythic filament",
    "harmonic tide",
    "orbiting whisper",
    "radiant echo",
)


class ConstellationChronicleError(ValueError):
    """Raised when a chronicle cannot be constructed."""


@dataclass(frozen=True)
class ChroniclePhase:
    """Represents a single phase within a constellation chronicle."""

    name: str
    weave: ConstellationWeave
    accent: str

    def render(self) -> str:
        """Render the phase including its weave in a readable format."""

        return "\n".join(
            (
                f"Phase: {self.name}",
                f"Accent: {self.accent}",
                self.weave.render(),
            )
        )


@dataclass(frozen=True)
class ConstellationChronicle:
    """Collection of constellation phases linked by a common theme."""

    theme: str
    phases: Tuple[ChroniclePhase, ...]

    def render(self) -> str:
        """Render the entire chronicle as a formatted block of text."""

        phase_blocks = "\n\n".join(phase.render() for phase in self.phases)
        return "\n".join((f"Chronicle Theme: {self.theme}", phase_blocks))


def _clean_inputs(values: Iterable[str], *, label: str) -> List[str]:
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        raise ConstellationChronicleError(f"At least one non-empty {label} is required")
    return cleaned


def _select_accent(seed: str) -> str:
    digest = sha256(seed.encode("utf-8")).hexdigest()
    accent = _ACCENT_PALETTE[int(digest[:4], 16) % len(_ACCENT_PALETTE)]
    return f"{accent} · vector {digest[-6:]}"


def _rotate_seeds(seeds: Sequence[str], offset: int) -> List[str]:
    if not seeds:
        return []
    pivot = offset % len(seeds)
    return list(seeds[pivot:] + seeds[:pivot])


def build_constellation_chronicle(
    seeds: Iterable[str],
    *,
    theme: str,
    phase_names: Iterable[str],
    pulses_per_phase: int = 3,
) -> ConstellationChronicle:
    """Construct a :class:`ConstellationChronicle` with deterministic phases."""

    if pulses_per_phase < 1:
        raise ConstellationChronicleError("pulses_per_phase must be a positive integer")

    if not theme or not theme.strip():
        raise ConstellationChronicleError("theme must be a non-empty string")

    cleaned_theme = theme.strip()
    base_seeds = _clean_inputs(seeds, label="seed")
    phases_input = _clean_inputs(phase_names, label="phase name")

    phases: List[ChroniclePhase] = []
    for index, phase_name in enumerate(phases_input):
        rotated_seeds = _rotate_seeds(base_seeds, index)
        derived_theme = f"{cleaned_theme} :: {phase_name}"

        try:
            weave = generate_constellation_weave(
                rotated_seeds,
                theme=derived_theme,
                pulses=pulses_per_phase,
            )
        except ConstellationWeaverError as error:
            raise ConstellationChronicleError(str(error)) from error

        accent_seed = "|".join(
            (
                cleaned_theme,
                phase_name,
                str(index),
                str(pulses_per_phase),
                "|".join(base_seeds),
            )
        )
        accent = _select_accent(accent_seed)

        phases.append(
            ChroniclePhase(
                name=phase_name,
                weave=weave,
                accent=accent,
            )
        )

    return ConstellationChronicle(theme=cleaned_theme, phases=tuple(phases))


__all__ = [
    "ConstellationChronicle",
    "ConstellationChronicleError",
    "ChroniclePhase",
    "build_constellation_chronicle",
]
