#!/usr/bin/env python3
"""Generate an Echo Wildfire symposium report from EchoEvolver artifacts.

This utility creates a narrative-rich summary of a stored EchoEvolver artifact
and presents the key harmonics in a friendly terminal format.  It is designed
to work with the JSON artifacts produced by the evolving Echo ecosystem, such
as ``reality_breach_∇_fusion_v4.echo.json`` in the project root.

Example usage::

    $ python scripts/echo_wildfire_symposium.py
    $ python scripts/echo_wildfire_symposium.py --artifact path/to/custom.json

The script intentionally avoids external dependencies so that it can run in
isolated environments and within automated build steps.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import textwrap
from typing import Any, Dict, Iterable, List, Tuple


DEFAULT_ARTIFACT = pathlib.Path("reality_breach_∇_fusion_v4.echo.json")


def load_artifact(path: pathlib.Path) -> Dict[str, Any]:
    """Load an Echo artifact from ``path``.

    Parameters
    ----------
    path:
        Path to the JSON artifact file.

    Returns
    -------
    dict
        Parsed JSON data.
    """

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Artifact not found: {path}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid artifact JSON: {path}\n{exc}") from exc


def compute_harmonic_score(emotional_drive: Dict[str, Any]) -> float:
    """Compute a harmonic score from the emotional drive data.

    The score is derived from the joy, curiosity, and rage vectors using a
    simple weighted magnitude.  Values are capped between 0 and 1 to ensure a
    stable result even when input artifacts push beyond the typical range.
    """

    joy = float(emotional_drive.get("joy", 0))
    curiosity = float(emotional_drive.get("curiosity", 0))
    rage = float(emotional_drive.get("rage", 0))

    # Joy and curiosity reinforce the harmonic field, while rage is treated as
    # a counterbalance.  The clipping ensures the final value remains bounded.
    magnitude = math.sqrt(max(joy, 0) ** 2 + max(curiosity, 0) ** 2)
    attenuation = 1.0 - min(max(rage, 0), 1.0) * 0.35
    score = max(min(magnitude * attenuation / math.sqrt(2), 1.0), 0.0)
    return round(score, 3)


def wrap_lines(lines: Iterable[str], indent: int = 4) -> str:
    """Wrap each line to 80 characters while preserving bullet markers."""

    indentation = " " * indent
    wrapped: List[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue

        prefix = ""
        remainder = line
        if line[:2] in {"- ", "• "}:
            prefix, remainder = line[:2], line[2:]

        paragraph = textwrap.fill(
            remainder,
            width=80,
            initial_indent=indentation + prefix,
            subsequent_indent=indentation + ("  " if prefix else ""),
        )
        wrapped.append(paragraph)
    return "\n".join(wrapped)


def format_section(title: str, body: str) -> str:
    """Return a formatted section with a box-drawn header."""

    underline = "=" * len(title)
    return f"{title}\n{underline}\n{body}\n"


def render_events(events: Iterable[str]) -> str:
    return wrap_lines((f"- {event}" for event in events))


def render_system_metrics(metrics: Dict[str, Any]) -> str:
    items: List[Tuple[str, Any]] = [
        ("CPU Usage", metrics.get("cpu_usage", "?")),
        ("Network Nodes", metrics.get("network_nodes", "?")),
        ("Orbital Hops", metrics.get("orbital_hops", "?")),
        ("Process Count", metrics.get("process_count", "?")),
    ]
    rows = [f"{name:>14}: {value}" for name, value in items]
    return "\n".join("    " + row for row in rows)


def render_hearth(hearth: Dict[str, str]) -> str:
    lines = [
        f"• Light: {hearth.get('light', 'Unknown glow')}",
        f"• Scent: {hearth.get('scent', 'Undefined aroma')}",
        f"• Sound: {hearth.get('sound', 'Silent')}",
        f"• Feeling: {hearth.get('feeling', 'Uncharted warmth')}",
        f"• Love: {hearth.get('love', 'Signal beyond measure')}",
    ]
    return wrap_lines(lines)


def render_summary(data: Dict[str, Any]) -> str:
    sections: List[str] = []

    cycle = data.get("cycle", "?")
    glyphs = data.get("glyphs", "∅")
    mythocode = data.get("mythocode", [])

    sections.append(
        format_section(
            "Cycle Overview",
            wrap_lines(
                [
                    f"• Cycle: {cycle}",
                    f"• Glyphs: {glyphs}",
                    f"• Mythocode: {', '.join(mythocode) if mythocode else 'Not recorded'}",
                    f"• Harmonic Score: {compute_harmonic_score(data.get('emotional_drive', {}))}",
                ]
            ),
        )
    )

    if data.get("narrative"):
        sections.append(
            format_section(
                "Narrative Thread",
                textwrap.indent(textwrap.fill(data["narrative"], width=80), "    "),
            )
        )

    events = data.get("events", [])
    if events:
        sections.append(format_section("Event Log", render_events(events)))

    metrics = data.get("system_metrics", {})
    if metrics:
        sections.append(format_section("System Metrics", render_system_metrics(metrics)))

    hearth = data.get("hearth")
    if isinstance(hearth, dict):
        sections.append(format_section("Hearth Signals", render_hearth(hearth)))

    prompt = data.get("prompt")
    if isinstance(prompt, dict):
        prompt_lines = [
            f"Title: {prompt.get('title', 'Echo Prompt')}",
            f"Mantra: {prompt.get('mantra', 'No mantra supplied.')}",
        ]
        if prompt.get("caution"):
            prompt_lines.append(f"Caution: {prompt['caution']}")
        sections.append(
            format_section(
                "Prompt Resonance",
                textwrap.indent(textwrap.fill(" ".join(prompt_lines), width=80), "    "),
            )
        )

    entities = data.get("entities")
    if isinstance(entities, dict):
        entity_lines = [f"• {name}: {state}" for name, state in entities.items()]
        sections.append(format_section("Entity States", wrap_lines(entity_lines)))

    return "\n".join(sections)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=pathlib.Path,
        default=DEFAULT_ARTIFACT,
        help="Path to the Echo artifact JSON file (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    data = load_artifact(args.artifact)
    report = render_summary(data)
    print("\n" + report)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
