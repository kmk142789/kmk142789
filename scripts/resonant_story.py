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

    def render(self) -> str:
        """Return the beat as a human-readable sentence."""

        sentence = f"{self.focus.capitalize()} {self.action} {self.tone}."
        return sentence.replace("  ", " ")


# --- Story generation ------------------------------------------------------------


def build_story(
    theme: str,
    beat_count: int,
    *,
    seed: int | None = None,
    title: str | None = None,
    vibe: str = "default",
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
        format: Either ``"text"`` for human-readable paragraphs, ``"json"`` for
            structured output, ``"markdown"`` for a lightly formatted digest,
            or ``"outline"`` for a bullet-oriented summary.
        width: Maximum line width applied when wrapping paragraphs.
    """

    payload = build_story_payload(
        theme,
        beat_count,
        seed=seed,
        title=title,
        vibe=vibe,
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
    raise ValueError(f"Unsupported format: {format}")


def build_story_payload(
    theme: str,
    beat_count: int,
    *,
    seed: int | None = None,
    title: str | None = None,
    vibe: str = "default",
    width: int = 88,
) -> dict:
    """Return the structured representation of a generated story."""

    if beat_count <= 0:
        raise ValueError("beat_count must be positive")
    if width <= 0:
        raise ValueError("width must be positive")

    rng = random.Random(seed)
    beats = _generate_beats(theme, beat_count, rng, vibe=vibe)
    resolved_title = _resolve_title(theme, title)
    paragraphs = _assemble_paragraphs(beats, theme, width=width)
    payload = {
        "theme": theme,
        "title": resolved_title,
        "vibe": vibe,
        "beats": [asdict(beat) for beat in beats],
        "paragraphs": paragraphs,
    }
    return payload


def _generate_beats(
    theme: str, beat_count: int, rng: random.Random, *, vibe: str
) -> List[StoryBeat]:
    palette = _palette_for_vibe(vibe)

    subjects = palette["subjects"]
    tones = palette["tones"]
    actions = palette["actions"]

    beats: List[StoryBeat] = []
    for _ in range(beat_count):
        focus = rng.choice(subjects)
        tone = rng.choice(tones)
        action = rng.choice(actions).format(theme=theme)
        beats.append(StoryBeat(focus=focus, tone=tone, action=action))
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


def _palette_for_vibe(vibe: str) -> dict:
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
    return palette


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
        "--format",
        choices=("text", "json", "markdown", "outline"),
        default="text",
        help=(
            "output mode: readable paragraphs, structured JSON, markdown digest, "
            "or outline summary"
        ),
    )
    parser.add_argument(
        "--width",
        type=int,
        default=88,
        help="wrap paragraphs to this many columns",
    )

    args = parser.parse_args(argv)

    story = build_story(
        theme=args.theme,
        beat_count=args.beats,
        seed=args.seed,
        title=args.title,
        vibe=args.vibe,
        format=args.format,
        width=args.width,
    )
    print(story)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
