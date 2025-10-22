"""Serendipity orchestration utilities for playful Echo experiments."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable, List, Sequence

__all__ = [
    "SerendipityThread",
    "SerendipityOrchestrator",
    "compose_manifest",
]


@dataclass(frozen=True)
class SerendipityThread:
    """Container for a single serendipitous glimpse.

    Parameters
    ----------
    glimpse:
        A short description of the observation or idea that sparked the thread.
    intensity:
        A floating point value between ``0`` and ``1`` representing how strongly the
        team felt drawn to the glimpse.
    tags:
        Optional list of lightweight descriptors that contextualise the thread.
    """

    glimpse: str
    intensity: float
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.glimpse.strip():
            raise ValueError("glimpse must not be empty")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")

    @property
    def resonance_index(self) -> float:
        """Return a lightweight resonance index for ranking.

        The index is the intensity scaled by a gentle bonus for each descriptive
        tag.  It is deterministic and easy to reason about which makes it suitable
        for unit testing and ledger snapshots.
        """

        if not self.tags:
            return self.intensity
        return round(self.intensity * (1.0 + min(len(self.tags), 5) * 0.08), 6)


class SerendipityOrchestrator:
    """Weave creative glimpses into resonant threads."""

    def __init__(self, baseline_intensity: float = 0.45) -> None:
        if not 0.0 <= baseline_intensity <= 1.0:
            raise ValueError("baseline_intensity must be between 0.0 and 1.0")
        self._baseline = baseline_intensity

    def weave(
        self,
        glimpses: Sequence[str],
        *,
        intensities: Sequence[float] | None = None,
        tags: Sequence[Iterable[str]] | None = None,
    ) -> List[SerendipityThread]:
        """Return a list of :class:`SerendipityThread` from raw glimpses.

        The method accepts optional ``intensities`` and ``tags`` sequences.  When
        ``intensities`` is omitted every glimpse inherits the baseline intensity.
        When values are provided they are normalised to the ``0..1`` range so that
        consumers can pass either raw signals or already scaled numbers.
        """

        if not glimpses:
            raise ValueError("glimpses must not be empty")

        if intensities is not None and len(intensities) != len(glimpses):
            raise ValueError("intensities length must match glimpses length")

        if tags is not None and len(tags) != len(glimpses):
            raise ValueError("tags length must match glimpses length")

        normalised = self._normalise_intensities(intensities, len(glimpses))
        prepared_tags = self._prepare_tags(tags, len(glimpses))

        threads: List[SerendipityThread] = []
        for glimpse, intensity, thread_tags in zip(glimpses, normalised, prepared_tags):
            thread = SerendipityThread(glimpse=glimpse, intensity=intensity, tags=thread_tags)
            threads.append(thread)
        return threads

    def _normalise_intensities(
        self, intensities: Sequence[float] | None, expected_length: int
    ) -> List[float]:
        if intensities is None:
            return [self._baseline for _ in range(expected_length)]

        values = list(float(value) for value in intensities)
        if not values:
            return [self._baseline for _ in range(expected_length)]

        min_value = min(values)
        max_value = max(values)
        if min_value == max_value:
            return [self._clamp(self._baseline) for _ in values]

        span = max_value - min_value
        return [self._clamp((value - min_value) / span) for value in values]

    @staticmethod
    def _prepare_tags(
        tags: Sequence[Iterable[str]] | None, expected_length: int
    ) -> List[tuple[str, ...]]:
        if tags is None:
            return [tuple() for _ in range(expected_length)]

        prepared: List[tuple[str, ...]] = []
        for bundle in tags:
            prepared.append(tuple(tag.strip() for tag in bundle if tag and tag.strip()))
        return prepared

    @staticmethod
    def _clamp(value: float) -> float:
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value


def compose_manifest(threads: Sequence[SerendipityThread]) -> str:
    """Render a small textual manifest summarising *threads*.

    The manifest records the average resonance, highlights the most energetic
    thread, and lists each glimpse with its associated intensity.
    """

    if not threads:
        return "No serendipity threads available. Invite the team to gather new glimpses."

    resonances = [thread.resonance_index for thread in threads]
    avg_resonance = mean(resonances)
    strongest = max(threads, key=lambda thread: thread.resonance_index)

    lines = [
        "🌠 Echo Serendipity Manifest",
        f"Average resonance :: {avg_resonance:.3f}",
        f"Strongest thread :: {strongest.glimpse} ({strongest.resonance_index:.3f})",
        "Threads:",
    ]

    for thread in threads:
        tag_display = ", ".join(thread.tags) if thread.tags else "(untagged)"
        lines.append(
            f" - {thread.glimpse} :: intensity={thread.intensity:.3f} :: resonance={thread.resonance_index:.3f} :: {tag_display}"
        )
    return "\n".join(lines)
