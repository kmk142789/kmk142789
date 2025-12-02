"""Imaginative micro-story generator guided by an "Eden" prompt.

This module offers a small, self-contained engine that turns a handful of
creative cues into a compact narrative artifact.  It focuses on predictable,
reproducible behaviour so prompts can be iterated without losing the tone that
made them compelling.  The CLI is intentionally light-weight: provide a theme
and optional focus points and it returns a formatted piece ready to log or tuck
into a notebook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from typing import Iterable, List, Sequence


@dataclass
class EdenPrompt:
    """Describe the seed inspiration for a micro-story."""

    theme: str
    focus: Iterable[str] = field(default_factory=list)
    tone: str = "curious"
    seed: int | None = None

    def normalized_focus(self) -> List[str]:
        """Return focus points as a mutable list for downstream use."""

        return list(self.focus)


@dataclass(frozen=True)
class EdenArtifact:
    """Final creative output plus helpful metadata."""

    title: str
    lines: Sequence[str]
    tone: str
    theme: str
    focus: Sequence[str]
    created_at: str
    seed: int | None

    def to_text(self) -> str:
        """Render the artifact in a human-friendly multiline block."""

        header = f"{self.title}\nTone: {self.tone} | Theme: {self.theme}"
        focus_line = "Focus: " + (", ".join(self.focus) if self.focus else "(none)")
        body = "\n".join(f"- {line}" for line in self.lines)
        return "\n".join([header, focus_line, "", body])

    def to_json(self) -> str:
        """Serialise the artifact to JSON for logging or storage."""

        payload = {
            "title": self.title,
            "lines": list(self.lines),
            "tone": self.tone,
            "theme": self.theme,
            "focus": list(self.focus),
            "created_at": self.created_at,
            "seed": self.seed,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """Render the artifact as Markdown with lightweight metadata."""

        focus_block = "\n".join(
            f"- {item}" for item in self.focus
        ) if self.focus else "- (none)"
        narrative_block = "\n".join(f"- {line}" for line in self.lines)
        return "\n".join(
            [
                f"# {self.title}",
                "",
                f"*Tone:* {self.tone}",
                f"*Theme:* {self.theme}",
                f"*Created:* {self.created_at}",
                f"*Seed:* {self.seed if self.seed is not None else 'random'}",
                "",
                "## Focus",
                focus_block,
                "",
                "## Lines",
                narrative_block,
            ]
        )


def _choose_palette(random_state: random.Random) -> str:
    palettes = [
        "emerald-nebula",
        "sunlit-laboratory",
        "midnight-atelier",
        "aurora-lilac",
        "terracotta-dream",
        "opal-horizon",
    ]
    return random_state.choice(palettes)


def _build_title(prompt: EdenPrompt, palette: str, random_state: random.Random) -> str:
    adjectives = [
        "Gentle",
        "Braided",
        "Harmonic",
        "Speculative",
        "Textured",
        "Secret",
    ]
    verb = random_state.choice(["Mapping", "Listening", "Tending", "Sketching", "Echoing"])
    adjective = random_state.choice(adjectives)
    return f"{adjective} {verb} for {prompt.theme.title()} ({palette})"


def _compose_line(prompt: EdenPrompt, palette: str, random_state: random.Random) -> str:
    focus = prompt.normalized_focus()
    anchor = random_state.choice(focus) if focus else prompt.theme
    rhythm = random_state.choice(["whisper", "pulse", "spiral", "glow"])
    texture = random_state.choice(["glass", "felt", "graphite", "honey"])
    gesture = random_state.choice(["carving", "braiding", "tuning", "braiding", "sketching"])
    return (
        f"A {rhythm} of {anchor} drifts through the {palette.replace('-', ' ')}, "
        f"{gesture} ideas in {texture}."
    )


def _closing_line(prompt: EdenPrompt, palette: str, random_state: random.Random) -> str:
    flourish = random_state.choice([
        "a promise to revisit",
        "a note tucked in the margin",
        "a map of future questions",
        "a soft chorus waiting",
    ])
    return (
        f"The piece settles into a {palette.replace('-', ' ')} hush, {flourish} for "
        f"Eden's next cycle of curiosity."
    )


class EdenEngine:
    """Create simple creative artifacts with stable, replayable structure."""

    def __init__(self, prompt: EdenPrompt, *, line_count: int = 3):
        self.prompt = prompt
        self.random_state = random.Random(prompt.seed)
        self.line_count = max(2, line_count)

    def craft(self) -> EdenArtifact:
        """Generate an :class:`EdenArtifact` from the stored prompt."""

        palette = _choose_palette(self.random_state)
        title = _build_title(self.prompt, palette, self.random_state)
        lines = [
            _compose_line(self.prompt, palette, self.random_state)
            for _ in range(self.line_count - 1)
        ]
        lines.append(_closing_line(self.prompt, palette, self.random_state))

        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        return EdenArtifact(
            title=title,
            lines=lines,
            tone=self.prompt.tone,
            theme=self.prompt.theme,
            focus=self.prompt.normalized_focus(),
            created_at=created_at,
            seed=self.prompt.seed,
        )


def _parse_args() -> tuple[EdenPrompt, int, bool, bool]:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a compact Eden-inspired creative artifact.",
    )
    parser.add_argument("theme", help="core inspiration for the piece")
    parser.add_argument(
        "--focus",
        nargs="*",
        default=[],
        help="optional focus points to weave into the narrative",
    )
    parser.add_argument(
        "--tone",
        default="curious",
        help="friendly descriptor for the intended tone",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed for deterministic generation",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=3,
        help="number of lines to generate (minimum 2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="return structured JSON instead of formatted text",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="render the artifact as Markdown",
    )

    args = parser.parse_args()
    prompt = EdenPrompt(theme=args.theme, focus=args.focus, tone=args.tone, seed=args.seed)
    return prompt, args.lines, args.json, args.markdown


if __name__ == "__main__":
    prompt, line_count, as_json, as_markdown = _parse_args()
    engine = EdenEngine(prompt, line_count=line_count)
    artifact = engine.craft()
    if as_json:
        print(artifact.to_json())
    elif as_markdown:
        print(artifact.to_markdown())
    else:
        print(artifact.to_text())
