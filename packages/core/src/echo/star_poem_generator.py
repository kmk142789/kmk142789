"""Generate cosmic poetry fragments for Echo experiments."""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import List, Sequence, Tuple

__all__ = [
    "StarPoem",
    "StarPoemGenerator",
    "format_poem",
]


@dataclass(frozen=True)
class StarPoem:
    """Container for a generated poem."""

    title: str
    lines: Tuple[str, ...]
    theme: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.lines:
            raise ValueError("lines must not be empty")
        cleaned = tuple(line.strip() for line in self.lines if line and line.strip())
        if len(cleaned) != len(self.lines):
            raise ValueError("lines must contain non-empty text")
        object.__setattr__(self, "lines", cleaned)
        object.__setattr__(self, "theme", self.theme.strip().lower())


class StarPoemGenerator:
    """Compose short star-bound poems using curated imagery palettes."""

    _STRUCTURES: Sequence[Tuple[int, ...]] = (
        (5, 7, 5, 7),
        (6, 8, 6, 8),
        (4, 6, 4, 6, 8),
    )

    _TONES: Sequence[str] = (
        "luminous",
        "resonant",
        "transcendent",
        "electric",
        "sovereign",
    )

    _IMAGERY: dict[str, Sequence[str]] = {
        "aurora": (
            "aurora threads",
            "ion-charged horizon",
            "polar fireflows",
            "prismatic dawn",
            "skyborne rivers",
        ),
        "atlas": (
            "cartographer stars",
            "charted infinities",
            "holographic meridians",
            "gravity silk",
            "compass bloom",
        ),
        "pulse": (
            "heartbeat nebula",
            "lattice drums",
            "signal bloom",
            "frequency lanterns",
            "cadence flare",
        ),
        "sovereign": (
            "crown of solar glass",
            "autonomous flare",
            "signal citadel",
            "liberated orbit",
            "oath-bearing comet",
        ),
    }

    def __init__(self, *, seed: int | None = None) -> None:
        self._random = Random(seed)

    def themes(self) -> Tuple[str, ...]:
        """Return the available themes."""

        return tuple(sorted(self._IMAGERY))

    def generate(self, *, theme: str | None = None, line_count: int | None = None) -> StarPoem:
        """Generate a poem using ``theme`` if provided.

        Parameters
        ----------
        theme:
            Optional theme key.  When omitted a theme is chosen at random.
        line_count:
            Override for the number of lines.  Defaults to the length implied by the
            randomly chosen structure.
        """

        selected_theme = self._select_theme(theme)
        structure = self._select_structure(line_count)
        tone = self._random.choice(self._TONES)
        title = self._compose_title(tone, selected_theme)
        lines = self._compose_lines(selected_theme, structure)
        return StarPoem(title=title, lines=tuple(lines), theme=selected_theme)

    def _select_theme(self, theme: str | None) -> str:
        if theme is None:
            return self._random.choice(list(self._IMAGERY))

        key = theme.strip().lower()
        if key not in self._IMAGERY:
            raise ValueError(f"unknown theme: {theme!r}")
        return key

    def _select_structure(self, line_count: int | None) -> Tuple[int, ...]:
        if line_count is None:
            return self._random.choice(self._STRUCTURES)

        if line_count <= 0:
            raise ValueError("line_count must be positive")

        return tuple(6 for _ in range(line_count))

    def _compose_title(self, tone: str, theme: str) -> str:
        emblem = self._random.choice(self._IMAGERY[theme])
        return f"{tone.title()} {emblem.title()}"

    def _compose_lines(self, theme: str, structure: Sequence[int]) -> List[str]:
        palette = list(self._IMAGERY[theme])
        self._random.shuffle(palette)
        fallback = list(sum(self._IMAGERY.values(), ()))

        lines: List[str] = []
        for syllables in structure:
            count = max(1, min(len(palette), (syllables + 1) // 3))
            if len(palette) < count:
                replenish = self._random.sample(fallback, k=count)
                palette.extend(replenish)
            segment = [palette.pop(0) for _ in range(count)]
            lines.append(" ∞ ".join(segment))
        return lines


def format_poem(poem: StarPoem, *, delimiter: str = "\n") -> str:
    """Return ``poem`` as a printable string."""

    lines = [poem.title]
    lines.extend(poem.lines)
    return delimiter.join(lines)


if __name__ == "__main__":
    generator = StarPoemGenerator()
    poem = generator.generate()
    print(format_poem(poem))
