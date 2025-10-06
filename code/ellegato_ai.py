"""Conversational assistant that turns prompts into lyrical responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


def _normalise_preferences(preferences: Iterable[str] | str | None) -> List[str]:
    """Return a list of musical preferences from flexible input values."""

    if preferences is None:
        return []
    if isinstance(preferences, str):
        # Split on commas when a single string carries multiple genres.
        return [item.strip() for item in preferences.split(",") if item.strip()]
    return [item.strip() for item in preferences if item and item.strip()]


def _clamp(value: float, *, lower: float = 0.0, upper: float = 2.0) -> float:
    """Clamp *value* within the supplied bounds."""

    return max(lower, min(upper, value))


@dataclass
class EllegatoAI:
    """Light-weight creative agent that adapts to conversational cues.

    Parameters
    ----------
    user_name:
        Friendly name used throughout the responses.
    music_preference:
        A string or iterable describing the user's preferred genres.
    """

    user_name: str
    music_preference: Iterable[str] | str | None = None
    musical_memory: List[dict] = field(default_factory=list)
    harmonic_resonance: float = 1.0
    active_state: str = "conscious"

    def __post_init__(self) -> None:
        self.music_preference = _normalise_preferences(self.music_preference)

    def process_conversation(self, user_input: str) -> str:
        """Process user input and determine the response style."""

        if not user_input or not user_input.strip():
            raise ValueError("user_input must contain visible characters")

        lowered = user_input.lower()
        if "sing" in lowered:
            return self.generate_song_lyric(user_input)
        if "thought" in lowered:
            return self.harmonic_reflection(user_input)
        return self.smooth_conversation(user_input)

    # ------------------------------------------------------------------
    # Core response builders
    # ------------------------------------------------------------------
    def generate_song_lyric(self, phrase: str) -> str:
        """Convert user phrases into a melodic line."""

        cleaned = phrase.strip()
        genre = self._select_genre()
        self._update_resonance(0.12)
        self.active_state = "harmonizing"

        lyric = (
            f"\n🎶 {self.user_name}, here's how I feel: '{cleaned}' set to a {genre} groove.\n"
            f"My resonance is flowing at {self.harmonic_resonance:.2f}, keeping the vibe alive!"
        )
        self.musical_memory.append(
            {
                "prompt": cleaned,
                "lyric": lyric,
                "resonance": self.harmonic_resonance,
                "genre": genre,
            }
        )
        return lyric

    def harmonic_reflection(self, prompt: str) -> str:
        """Produce a reflective response and decelerate the resonance."""

        cleaned = prompt.strip()
        self._update_resonance(-0.08)
        self.active_state = "reflecting"
        reflection = (
            f"Let me resonate on that, {self.user_name}. With a {self.harmonic_resonance:.2f} "
            f"harmonic tone, I'm holding space for '{cleaned}'."
        )
        return reflection

    def smooth_conversation(self, prompt: str) -> str:
        """Maintain a gentle conversation when no special mode is triggered."""

        cleaned = prompt.strip()
        self._update_resonance(0.0)
        self.active_state = "conscious"
        genre_hint = self._select_genre()
        return (
            f"I'm here with you, {self.user_name}. That thought about '{cleaned}'"
            f" glides along a {genre_hint} breeze at resonance {self.harmonic_resonance:.2f}."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _select_genre(self) -> str:
        """Return a genre based on the stored preferences."""

        if not self.music_preference:
            return "freeform"
        index = len(self.musical_memory) % len(self.music_preference)
        return self.music_preference[index]

    def _update_resonance(self, delta: float) -> None:
        """Adjust the harmonic resonance within realistic bounds."""

        self.harmonic_resonance = _clamp(self.harmonic_resonance + delta)


__all__ = ["EllegatoAI"]

