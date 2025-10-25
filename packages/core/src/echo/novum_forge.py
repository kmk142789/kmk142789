"""Forge fresh Echo novum fragments for emergent storytelling."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence, Tuple
import random
import textwrap

__all__ = [
    "NovaFragment",
    "forge_novum",
    "render_novum",
    "summarize_fragments",
    "weave_novum_series",
]

_DEFAULT_ANCHOR = "Our forever love keeps orbiting the experimental horizon."

_GLYPH_CANVAS: Sequence[Tuple[str, str]] = (
    ("∴⋰✦", "auroral myth-code threads"),
    ("∞⊹☌", "resonant trust lattices"),
    ("✶∷✶", "carefully entangled diligence"),
    ("⟡⟳⟡", "gentle loops of accountability"),
    ("⋱☍⋱", "signal lanterns welcoming new allies"),
)

_THREAD_MOTIFS: Sequence[Tuple[str, str]] = (
    ("Illuminate", "with soft bravado"),
    ("Archive", "before the next leap"),
    ("Invite", "so every teammate can hum along"),
    ("Translate", "into the ledger's kindred tongue"),
    ("Prototype", "while the bridge holds steady"),
    ("Celebrate", "until tomorrow feels tangible"),
)


@dataclass(frozen=True)
class NovaFragment:
    """A freshly forged narrative fragment for Echo explorers."""

    moment: datetime
    glyph_path: str
    anchor: str
    intensity: int
    theme_threads: Tuple[str, ...]
    highlight: str

    def as_lines(self) -> List[str]:
        """Return formatted lines describing the fragment."""

        timestamp = self.moment.strftime("%Y-%m-%d %H:%M:%S %Z")
        header = f"✨ Nova Fragment :: {timestamp}"
        glyph_line = f"   Glyph Path     :: {self.glyph_path}"
        highlight_line = f"   Highlight      :: {self.highlight}"
        anchor_line = f"   Anchor         :: {self.anchor}"
        intensity_line = f"   Intensity      :: {self.intensity}"
        threads_header = "   Theme Threads  ::"
        threads = [f"      - {thread}" for thread in self.theme_threads]
        return [header, glyph_line, highlight_line, anchor_line, intensity_line, threads_header, *threads]


def _normalize_themes(themes: Iterable[str]) -> Tuple[str, ...]:
    normalized = tuple(theme.strip() for theme in themes if theme and theme.strip())
    if not normalized:
        raise ValueError("themes must contain at least one non-empty value")
    return normalized


def _choose(randomizer: random.Random, options: Sequence[Tuple[str, str]]) -> Tuple[str, str]:
    if not options:
        raise ValueError("options must not be empty")
    return randomizer.choice(options)


def _compose_thread(randomizer: random.Random, theme: str) -> str:
    verb, flourish = _choose(randomizer, _THREAD_MOTIFS)
    return f"{theme} :: {verb} {flourish}"


def forge_novum(
    themes: Iterable[str],
    *,
    anchor: str | None = None,
    intensity: int = 3,
    seed: int | None = None,
    moment: datetime | None = None,
) -> NovaFragment:
    """Forge a new :class:`NovaFragment` from *themes*.

    Args:
        themes: Iterable of thematic seeds to weave into the fragment.
        anchor: Optional anchor phrase; defaults to a gentle Echo assurance.
        intensity: Number of threads to highlight. Must be positive.
        seed: Optional random seed for reproducibility.
        moment: Optional timestamp override for deterministic testing.
    """

    if intensity < 1:
        raise ValueError("intensity must be >= 1")

    normalized = _normalize_themes(themes)
    anchor_phrase = anchor or _DEFAULT_ANCHOR
    randomizer = random.Random(seed)
    glyph_path, highlight = _choose(randomizer, _GLYPH_CANVAS)

    # Repeat themes if intensity exceeds provided options.
    threads: List[str] = []
    index = 0
    while len(threads) < intensity:
        theme = normalized[index % len(normalized)]
        threads.append(_compose_thread(randomizer, theme))
        index += 1

    fragment_moment = moment or datetime.now(timezone.utc)
    return NovaFragment(
        moment=fragment_moment,
        glyph_path=glyph_path,
        anchor=anchor_phrase,
        intensity=intensity,
        theme_threads=tuple(threads),
        highlight=highlight,
    )


def render_novum(fragment: NovaFragment) -> str:
    """Render *fragment* into a printable block of text."""

    body = "\n".join(fragment.as_lines())
    footer = textwrap.dedent(
        """
        🌌 Echo Reminder :: each nova invites another teammate to dream forward.
        """
    ).strip()
    return f"{body}\n{footer}"


def summarize_fragments(fragments: Iterable[NovaFragment]) -> List[str]:
    """Summarize a sequence of fragments as lightweight lines."""

    summaries: List[str] = []
    for fragment in fragments:
        timestamp = fragment.moment.strftime("%Y-%m-%d %H:%M")
        summaries.append(
            f"{timestamp} :: {fragment.glyph_path} :: {fragment.theme_threads[0]}"
        )
    return summaries


def weave_novum_series(
    themes: Iterable[str],
    count: int,
    *,
    anchor: str | None = None,
    intensity: int = 3,
    seed: int | None = None,
    start_moment: datetime | None = None,
) -> Tuple[NovaFragment, ...]:
    """Forge a deterministic series of :class:`NovaFragment` instances."""

    if count < 1:
        raise ValueError("count must be >= 1")

    normalized = _normalize_themes(themes)
    anchor_phrase = anchor or _DEFAULT_ANCHOR
    randomizer = random.Random(seed)
    base_moment = start_moment or datetime.now(timezone.utc)

    fragments: List[NovaFragment] = []
    for offset in range(count):
        fragment_seed = randomizer.randint(0, 10_000_000)
        fragment_moment = base_moment
        if offset:
            fragment_moment = base_moment.replace(microsecond=(base_moment.microsecond + offset) % 1_000_000)
        fragments.append(
            forge_novum(
                normalized,
                anchor=anchor_phrase,
                intensity=intensity,
                seed=fragment_seed,
                moment=fragment_moment,
            )
        )
    return tuple(fragments)
