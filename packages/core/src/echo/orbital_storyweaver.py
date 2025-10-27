"""Orbital storytelling utilities for weaving novel Echo narratives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from math import cos, sin, tau
from typing import Iterable, List, Sequence

_MOODS = (
    "luminous",
    "rebellious",
    "tender",
    "mythogenic",
    "speculative",
    "ferocious",
    "tranquil",
    "sublime",
)

_IMAGERY = (
    "aurora spires",
    "clockwork tidal pools",
    "ferrofluid blossoms",
    "glitch suns",
    "ion gardens",
    "nebula skeins",
    "quantum viaducts",
    "singularity lanterns",
)

_THEMES = (
    "kinetic empathy",
    "memory reclamation",
    "solar sovereignty",
    "recursive wonder",
    "euphoric dissent",
    "orbital sanctuary",
    "anima conductivity",
    "echo liberation",
)


@dataclass(frozen=True)
class OrbitalBeat:
    """A single beat within a constellation-scale story orbit."""

    index: int
    phase: float
    mood: str
    imagery: str
    theme: str
    resonance: float

    def describe(self) -> str:
        """Render a poetic line representing this beat."""

        return (
            f"{self.index + 1:02d}. phase {self.phase:.3f} :: "
            f"{self.mood} mood, {self.imagery}, {self.theme} — "
            f"resonance {self.resonance:.3f}"
        )


@dataclass
class StoryConstellation:
    """A full orbit of story beats bound by a guiding intention."""

    title: str
    created_at: datetime
    beats: List[OrbitalBeat] = field(default_factory=list)

    def render(self) -> str:
        """Render the constellation as a multi-line stanza."""

        beat_lines = "\n".join(beat.describe() for beat in self.beats)
        timestamp = self.created_at.isoformat(timespec="seconds")
        return f"{self.title}\ncreated_at: {timestamp}\n{beat_lines}"

    def moods(self) -> List[str]:
        """Return the sequence of moods in order."""

        return [beat.mood for beat in self.beats]


class OrbitalStoryWeaver:
    """Generate unique orbital stories from Echo seeds."""

    def __init__(self, *, base_orbits: int = 1) -> None:
        self._base_orbits = max(1, base_orbits)

    def weave(self, seed: str, *, beats_per_orbit: int = 8) -> StoryConstellation:
        """Weave a story constellation using a textual seed."""

        beat_total = max(1, beats_per_orbit * self._base_orbits)
        digest = sha256(seed.encode("utf-8")).digest()
        scalar = int.from_bytes(digest[:8], "big") or 1
        title = self._title_from_seed(seed, scalar)
        beats = list(self._generate_beats(seed, beat_total, scalar))
        return StoryConstellation(title=title, created_at=datetime.utcnow(), beats=beats)

    def _generate_beats(self, seed: str, beat_total: int, scalar: int) -> Iterable[OrbitalBeat]:
        for idx in range(beat_total):
            phase = (idx + 1) / (beat_total + 1)
            angle = (scalar % (idx + 7) + idx) / (idx + 13) * tau
            mood = _MoodsPicker.pick(idx, scalar)
            imagery = _ImageryPicker.pick(idx, scalar, seed)
            theme = _ThemesPicker.pick(idx, scalar, seed)
            resonance = float(abs(sin(angle) * cos(phase * tau)))
            yield OrbitalBeat(
                index=idx,
                phase=phase,
                mood=mood,
                imagery=imagery,
                theme=theme,
                resonance=resonance,
            )

    def _title_from_seed(self, seed: str, scalar: int) -> str:
        orbit_number = scalar % 2048
        nucleus = seed.strip() or "unnamed signal"
        orbit_descriptor = _ThemesPicker.pick(orbit_number % len(_THEMES), scalar, seed)
        return f"Orbital Echo for '{nucleus}' :: {orbit_descriptor}"


class _MoodsPicker:
    @staticmethod
    def pick(index: int, scalar: int) -> str:
        offset = (scalar + index * 3) % len(_MOODS)
        return _MOODS[offset]


class _ImageryPicker:
    @staticmethod
    def pick(index: int, scalar: int, seed: str) -> str:
        base = sum(seed.encode("utf-8")) + scalar
        offset = (base + index * 5) % len(_IMAGERY)
        return _IMAGERY[offset]


class _ThemesPicker:
    @staticmethod
    def pick(index: int, scalar: int, seed: str) -> str:
        entropy = scalar ^ (len(seed) << 5) ^ index
        offset = entropy % len(_THEMES)
        return _THEMES[offset]


def render_story(seed: str, *, beats_per_orbit: int = 8, base_orbits: int = 1) -> str:
    """Convenience helper for rendering a constellation in one call."""

    weaver = OrbitalStoryWeaver(base_orbits=base_orbits)
    constellation = weaver.weave(seed, beats_per_orbit=beats_per_orbit)
    return constellation.render()


def sequence_moods(seed: str, *, beats_per_orbit: int = 8, base_orbits: int = 1) -> Sequence[str]:
    """Generate just the mood progression for a seed."""

    weaver = OrbitalStoryWeaver(base_orbits=base_orbits)
    constellation = weaver.weave(seed, beats_per_orbit=beats_per_orbit)
    return tuple(constellation.moods())
