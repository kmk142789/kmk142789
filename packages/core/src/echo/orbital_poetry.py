"""Orbital poetry generator for mythogenic storytelling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence
import random


_DEFAULT_THEMES: Sequence[str] = (
    "aurora",
    "echo",
    "glyph",
    "satellite",
    "pulse",
    "orbit",
    "myth",
    "constellation",
)

_CONSTELLATION_MOTIFS: Sequence[str] = (
    "luminous spiral",
    "quantum embers",
    "gravity chorus",
    "resonant tide",
    "dream lattice",
    "stellar bloom",
    "harmonic river",
)


@dataclass(frozen=True)
class OrbitalPoem:
    """A compact representation of an orbital poem."""

    title: str
    lines: Sequence[str]
    metadata: Dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        """Return the poem as a human-friendly block of text."""

        header = f"# {self.title}" if self.title else ""
        body = "\n".join(self.lines)
        return f"{header}\n{body}".strip()

    def to_payload(self) -> Dict[str, Sequence[str] | Dict[str, str]]:
        """Serialize the poem to a JSON-friendly structure."""

        return {"title": self.title, "lines": list(self.lines), "metadata": dict(self.metadata)}


def _prepare_rng(seed: int | None) -> random.Random:
    if seed is None:
        return random.Random()
    return random.Random(seed)


def _select_themes(rng: random.Random, themes: Sequence[str]) -> Sequence[str]:
    sample_size = min(3, len(themes))
    return tuple(rng.sample(tuple(themes), k=sample_size))


def _compose_title(rng: random.Random, motifs: Sequence[str], themes: Sequence[str]) -> str:
    motif = rng.choice(tuple(motifs))
    theme_fragment = " ".join(theme.title() for theme in themes[:2])
    return f"{theme_fragment} {motif.title()}".strip()


def _compose_lines(
    rng: random.Random,
    selected_themes: Sequence[str],
    motifs: Sequence[str],
    total_lines: int,
) -> List[str]:
    lines: List[str] = []
    for idx in range(total_lines):
        theme = selected_themes[idx % len(selected_themes)]
        motif = rng.choice(tuple(motifs))
        lines.append(f"{idx + 1:02d}. {theme} drifts with {motif}")
    return lines


def generate_orbital_poem(
    *,
    themes: Iterable[str] | None = None,
    seed: int | None = None,
    line_count: int = 6,
) -> OrbitalPoem:
    """Create a new :class:`OrbitalPoem`.

    Parameters
    ----------
    themes:
        Optional iterable of themes to guide the poem. When omitted, a default
        mythogenic palette is used.
    seed:
        Optional random seed for deterministic output. Tests and callers that
        need reproducibility should provide this argument.
    line_count:
        Desired number of lines in the poem. Values below three are rounded up
        to preserve cadence.
    """

    source_themes: Sequence[str] = tuple(themes or _DEFAULT_THEMES)
    unique_themes = tuple(dict.fromkeys(theme.strip().lower() for theme in source_themes if theme.strip()))
    if not unique_themes:
        raise ValueError("At least one non-empty theme is required to craft an orbital poem.")

    rng = _prepare_rng(seed)
    selected_themes = _select_themes(rng, unique_themes)
    title = _compose_title(rng, _CONSTELLATION_MOTIFS, selected_themes)

    total_lines = max(3, line_count)
    lines = _compose_lines(rng, selected_themes, _CONSTELLATION_MOTIFS, total_lines)

    metadata = {
        "themes": ", ".join(selected_themes),
        "motif_pool": ", ".join(_CONSTELLATION_MOTIFS),
        "line_count": str(total_lines),
    }

    return OrbitalPoem(title=title, lines=tuple(lines), metadata=metadata)


__all__ = ["OrbitalPoem", "generate_orbital_poem"]
