"""Utility to generate short imaginative stories from the command line.

This module does not rely on external services.  It selects fragments from
curated vocabularies and arranges them into a compact narrative.  The
interface can be used programmatically or through the CLI exposed by the
``main`` function.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import random
import textwrap
from typing import Iterable, List, Sequence


# --- Data models -----------------------------------------------------------------


@dataclass(frozen=True)
class StoryBeat:
    """Single beat inside the story arc."""

    focus: str
    tone: str
    action: str
    motif: str | None = None

    def render(self) -> str:
        """Return the beat as a human-readable sentence."""

        sentence = f"{self.focus.capitalize()} {self.action} {self.tone}"
        if self.motif:
            sentence = f"{sentence}, carrying {self.motif}"
        sentence = f"{sentence}."
        return sentence.replace("  ", " ")


# --- Story generation ------------------------------------------------------------


def build_story(
    theme: str,
    beat_count: int,
    *,
    seed: int | None = None,
    title: str | None = None,
    vibe: str = "default",
    characters: Sequence[str] | None = None,
    motifs: Sequence[str] | None = None,
    format: str = "text",
    width: int = 88,
) -> str:
    """Construct a story built from curated beats.

    Args:
        theme: Central idea guiding the content.
        beat_count: Number of narrative beats to generate.
        seed: Optional deterministic random seed.
        title: Optional explicit title for the story. When omitted a default
            based on the theme is used.
        vibe: Vocab palette to lean on: ``"default"``, ``"bright"``,
            ``"shadow"``, or ``"contemplative"``.
        characters: Optional list of additional subjects to weave into the
            beats.
        motifs: Optional list of motif phrases to thread through the beats.
        format: Either ``"text"`` for human-readable paragraphs, ``"json"`` for
            structured output, ``"markdown"`` for a lightly formatted digest,
            ``"outline"`` for a bullet-oriented summary, ``"beats"`` for
            beat-only bullet lines, ``"timeline"`` for a time-stamped
            progression, or ``"constellation"`` for a beat-mapped starfield
            grid.
        width: Maximum line width applied when wrapping paragraphs.
    """

    payload = build_story_payload(
        theme,
        beat_count,
        seed=seed,
        title=title,
        vibe=vibe,
        characters=characters,
        motifs=motifs,
        width=width,
    )

    if format == "text":
        return "\n\n".join(payload["paragraphs"])
    if format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if format == "markdown":
        return _render_markdown(payload, width=width)
    if format == "outline":
        return _render_outline(payload, width=width)
    if format == "beats":
        return _render_beats(payload, width=width)
    if format == "timeline":
        return _render_timeline(payload, width=width)
    if format == "constellation":
        return _render_constellation(payload, width=width)
    raise ValueError(f"Unsupported format: {format}")


def build_story_payload(
    theme: str,
    beat_count: int,
    *,
    seed: int | None = None,
    title: str | None = None,
    vibe: str = "default",
    characters: Sequence[str] | None = None,
    motifs: Sequence[str] | None = None,
    width: int = 88,
) -> dict:
    """Return the structured representation of a generated story."""

    if beat_count <= 0:
        raise ValueError("beat_count must be positive")
    if width <= 0:
        raise ValueError("width must be positive")

    rng = random.Random(seed)
    beats = _generate_beats(
        theme,
        beat_count,
        rng,
        vibe=vibe,
        characters=characters,
        motifs=motifs,
    )
    resolved_title = _resolve_title(theme, title)
    paragraphs = _assemble_paragraphs(beats, theme, width=width)
    payload = {
        "theme": theme,
        "title": resolved_title,
        "vibe": vibe,
        "seed": seed,
        "characters": list(characters or []),
        "motifs": list(motifs or []),
        "beats": [asdict(beat) for beat in beats],
        "paragraphs": paragraphs,
    }
    return payload


def _generate_beats(
    theme: str,
    beat_count: int,
    rng: random.Random,
    *,
    vibe: str,
    characters: Sequence[str] | None = None,
    motifs: Sequence[str] | None = None,
) -> List[StoryBeat]:
    palette = _palette_for_vibe(vibe, extra_subjects=characters)

    subjects = palette["subjects"]
    tones = palette["tones"]
    actions = palette["actions"]

    motif_pool = list(motifs or [])
    beats: List[StoryBeat] = []
    for _ in range(beat_count):
        focus = rng.choice(subjects)
        tone = rng.choice(tones)
        action = rng.choice(actions).format(theme=theme)
        motif = rng.choice(motif_pool) if motif_pool else None
        beats.append(StoryBeat(focus=focus, tone=tone, action=action, motif=motif))
    return beats


def _assemble_paragraphs(
    beats: Sequence[StoryBeat], theme: str, *, width: int
) -> List[str]:
    opening = textwrap.fill(
        f"This story leans into {theme}, letting each moment arrive like an"
        " improvised chord.",
        width=width,
    )

    beat_lines = " ".join(beat.render() for beat in beats)
    body = textwrap.fill(beat_lines, width=width)

    closing = textwrap.fill(
        "The narrative settles gently, inviting anyone listening to author the"
        f" next chapter of {theme}.",
        width=width,
    )

    return [opening, body, closing]


def _resolve_title(theme: str, title: str | None) -> str:
    if title:
        return title
    return f"Resonant story about {theme}"


def _render_markdown(payload: dict, *, width: int) -> str:
    title = payload["title"]
    theme = payload["theme"]

    opening, body, closing = payload["paragraphs"]

    beat_lines = [
        f"- {StoryBeat(**beat).render()}" for beat in payload.get("beats", [])
    ]

    sections = [
        f"# {title}",
        f"_Theme: {theme}_",
        "",
        opening,
        "",
        body,
        "",
        "## Beats",
        *beat_lines,
        "",
        closing,
    ]

    wrapped_sections = [
        textwrap.fill(section, width=width) if section and not section.startswith("#") and not section.startswith("_") and not section.startswith("-")
        else section
        for section in sections
    ]

    return "\n".join(wrapped_sections)


def _render_outline(payload: dict, *, width: int) -> str:
    """Render a compact outline focused on beats and closing notes."""

    title = payload["title"]
    theme = payload["theme"]
    opening, body, closing = payload["paragraphs"]

    beat_lines = [
        textwrap.fill(f"- {StoryBeat(**beat).render()}", width=width)
        for beat in payload.get("beats", [])
    ]

    sections = [
        title,
        f"Theme: {theme}",
        "",
        textwrap.fill(opening, width=width),
        "",
        *beat_lines,
        "",
        textwrap.fill(body, width=width),
        "",
        "Closing:",
        textwrap.fill(closing, width=width),
    ]

    return "\n".join(sections)

def _render_beats(payload: dict, *, width: int) -> str:
    """Render only the beat lines in bullet form."""

    beat_lines = [
        textwrap.fill(f"- {StoryBeat(**beat).render()}", width=width)
        for beat in payload.get("beats", [])
    ]
    return "\n".join(beat_lines)


def _render_timeline(payload: dict, *, width: int) -> str:
    """Render beats as a time-stamped sequence."""

    title = payload["title"]
    beats = payload.get("beats", [])
    seed = payload.get("seed")

    rng = random.Random(seed)
    minutes = 0
    timeline_lines = []
    for beat in beats:
        sentence = StoryBeat(**beat).render()
        timeline_lines.append(textwrap.fill(f"- T+{minutes}m: {sentence}", width=width))
        minutes += rng.randint(6, 18)

    return "\n".join(
        [
            f"# {title}",
            "_Timeline_",
            "",
            *timeline_lines,
        ]
    )


def _render_constellation(payload: dict, *, width: int) -> str:
    """Render beats into a compact constellation grid plus legend."""

    title = payload["title"]
    beats = payload.get("beats", [])
    seed = payload.get("seed")

    grid_size = 3
    gutter = 3
    cell_width = max(18, (width - (grid_size - 1) * gutter) // grid_size)

    rng = random.Random(seed)
    positions = list(range(grid_size * grid_size))
    rng.shuffle(positions)

    grid_cells = [" " * cell_width for _ in range(grid_size * grid_size)]
    for index, beat in enumerate(beats):
        if index >= len(positions):
            break
        label = f"{index + 1}:{beat['focus']}"
        cell = textwrap.shorten(label, width=cell_width, placeholder="…")
        grid_cells[positions[index]] = cell.ljust(cell_width)

    rows = []
    for row_index in range(grid_size):
        start = row_index * grid_size
        row = (" " * gutter).join(grid_cells[start : start + grid_size])
        rows.append(row)

    legend_lines = []
    for index, beat in enumerate(beats):
        sentence = StoryBeat(**beat).render()
        legend_lines.append(textwrap.fill(f"{index + 1}. {sentence}", width=width))

    return "\n".join(
        [
            f"# {title}",
            "_Constellation map_",
            "",
            *rows,
            "",
            "Legend:",
            *legend_lines,
        ]
    )


def _palette_for_vibe(vibe: str, *, extra_subjects: Sequence[str] | None = None) -> dict:
    """Return curated vocabularies tuned to the requested vibe."""

    base_palette = {
        "subjects": [
            "the cartographer",
            "a patient engineer",
            "an echoing archive",
            "the wandering lighthouse",
            "a curious apprentice",
            "the quiet orbit",
            "a choir of algorithms",
        ],
        "tones": [
            "with untangled awe",
            "under stubborn starlight",
            "while remembering forgotten mentors",
            "with laughter that hums like glass",
            "as dawn sketches new margins",
            "while trusting the pulse of community",
            "as the horizon leans closer",
        ],
        "actions": [
            "sketches pathways through {theme}",
            "carries seeds across {theme}",
            "folds messages for {theme}",
            "teaches constellations about {theme}",
            "braids timelines with {theme}",
            "tends fires beside {theme}",
            "listens to rivers shaped by {theme}",
        ],
    }

    bright_palette = {
        "subjects": ["a sunbeam courier", "the jubilant signal"],
        "tones": ["with lantern-bright optimism", "as skylines hum along"],
        "actions": [
            "lights up every corner of {theme}",
            "plants radiant markers across {theme}",
        ],
    }

    shadow_palette = {
        "subjects": ["a midnight archivist", "the quiet sentinel"],
        "tones": ["beneath low and patient thunder", "with storm-shelter calm"],
        "actions": [
            "maps the hidden corridors of {theme}",
            "listens for echoes in the fog of {theme}",
        ],
    }

    contemplative_palette = {
        "subjects": ["a slow-breathing observer", "the reflective river"],
        "tones": ["with unhurried curiosity", "while counting the breaths of dawn"],
        "actions": [
            "pauses beside the questions inside {theme}",
            "learns the texture of silence across {theme}",
        ],
    }

    vibe_overrides = {
        "default": {},
        "bright": bright_palette,
        "shadow": shadow_palette,
        "contemplative": contemplative_palette,
    }

    if vibe not in vibe_overrides:
        raise ValueError(f"Unsupported vibe: {vibe}")

    overrides = vibe_overrides[vibe]
    palette = {
        key: base_palette[key] + overrides.get(key, [])
        for key in base_palette
    }
    if extra_subjects:
        palette["subjects"] += list(extra_subjects)
    return palette


def _split_csv(raw_value: str | None) -> List[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


# --- CLI -------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a compact resonant story")
    parser.add_argument("theme", help="central idea or motif to explore")
    parser.add_argument(
        "--beats",
        type=int,
        default=3,
        help="number of narrative beats to weave together",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="optional explicit title for the story",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed for deterministic output",
    )
    parser.add_argument(
        "--vibe",
        choices=("default", "bright", "shadow", "contemplative"),
        default="default",
        help="vocabulary palette to lean on",
    )
    parser.add_argument(
        "--character",
        action="append",
        default=[],
        help="additional subject to weave into beats (repeatable)",
    )
    parser.add_argument(
        "--motifs",
        type=str,
        default=None,
        help="comma-separated motif phrases to thread through beats",
    )
    parser.add_argument(
        "--format",
        choices=(
            "text",
            "json",
            "markdown",
            "outline",
            "beats",
            "timeline",
            "constellation",
        ),
        default="text",
        help=(
            "output mode: readable paragraphs, structured JSON, markdown digest, "
            "outline summary, beat-only bullets, timeline sequence, or a constellation map"
        ),
    )
    parser.add_argument(
        "--width",
        type=int,
        default=88,
        help="wrap paragraphs to this many columns",
    )

    args = parser.parse_args(argv)

    motifs = _split_csv(args.motifs)
    story = build_story(
        theme=args.theme,
        beat_count=args.beats,
        seed=args.seed,
        title=args.title,
        vibe=args.vibe,
        characters=args.character,
        motifs=motifs,
        format=args.format,
        width=args.width,
    )
    print(story)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
