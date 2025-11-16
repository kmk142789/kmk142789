"""Creative loop generator for playful improvisations.

This module creates short clusters of statements that orbit around a motif.
Each loop is designed to feel rhythmic, blending observational language with
imaginative declarations.  The module can be imported as a library or used
from the command line to print a loop to stdout.

Version two deepens the internal representation by modelling rhythm patterns
and diagnostics.  :class:`LoopRhythm` instances capture syncopation accents and
tempo variations that shape each generated sentence.  The accompanying
:class:`LoopDiagnostics` records metadata that can be inspected by external
systems to understand which narrative voices and fragments were emphasised.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import random
from typing import Dict, Iterable, List, Tuple


VOICE_LIBRARY = [
    "observer",
    "cartographer",
    "chorus",
    "wanderer",
    "signal",
    "dream",
]


@dataclass
class LoopSeed:
    """Parameters that describe the creative loop we want to generate."""

    motif: str
    fragments: Iterable[str] = field(default_factory=list)
    tempo: str = "andante"
    pulses: int = 3
    seed: int | None = None
    voice_bias: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.fragments = list(self.fragments)
        if self.pulses < 1:
            raise ValueError("pulses must be positive")
        if self.voice_bias:
            cleaned_bias: Dict[str, float] = {}
            for voice, weight in self.voice_bias.items():
                if voice not in VOICE_LIBRARY:
                    continue
                try:
                    numeric_weight = float(weight)
                except (TypeError, ValueError):
                    continue
                if numeric_weight <= 0:
                    continue
                cleaned_bias[voice] = numeric_weight
            self.voice_bias = cleaned_bias


@dataclass
class LoopRhythm:
    """Encapsulate syncopation, tempo variance, and pulse metadata."""

    tempo: str
    pulses: int
    accents: List[int]
    dynamic_tempi: List[str]

    def accent_for(self, index: int) -> int:
        return self.accents[index % len(self.accents)]

    def tempo_for(self, index: int) -> str:
        return self.dynamic_tempi[index % len(self.dynamic_tempi)]


@dataclass
class LoopDiagnostics:
    """Record metadata about the generated loop for downstream tooling."""

    voices: Counter[str] = field(default_factory=Counter)
    fragments: Counter[str] = field(default_factory=Counter)
    accents: List[int] = field(default_factory=list)

    def register(self, voice: str, fragment: str | None, accent: int) -> None:
        self.voices[voice] += 1
        if fragment:
            self.fragments[fragment] += 1
        self.accents.append(accent)

    def render_report(self) -> str:
        ordered_voices = ", ".join(f"{voice}:{count}" for voice, count in self.voices.items())
        ordered_fragments = ", ".join(
            f"{fragment}:{count}" for fragment, count in self.fragments.most_common(3)
        )
        accent_profile = ",".join(str(value) for value in self.accents)
        return (
            f"Voices[{ordered_voices}] | Fragments[{ordered_fragments or 'none'}] | Accents[{accent_profile}]"
        )

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the diagnostics."""

        return {
            "voices": dict(self.voices),
            "fragments": dict(self.fragments),
            "accents": list(self.accents),
        }


@dataclass
class LoopSummary:
    """Capture high-level metrics about the rendered loop."""

    voice_diversity: float
    accent_focus: float
    dominant_voice: str | None
    fragment_coverage: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "voice_diversity": self.voice_diversity,
            "accent_focus": self.accent_focus,
            "dominant_voice": self.dominant_voice,
            "fragment_coverage": self.fragment_coverage,
        }


@dataclass
class LoopResult:
    """Bundle the generated lines with diagnostics and rhythm metadata."""

    lines: List[str]
    diagnostics: LoopDiagnostics
    rhythm: LoopRhythm
    timeline: List[Dict[str, object]] = field(default_factory=list)
    summary: LoopSummary | None = None

    def render(self) -> List[str]:
        diagnostic_line = f"[diagnostics] {self.diagnostics.render_report()}"
        rhythm_line = (
            "Rhythm Pattern: "
            + ",".join(str(value) for value in self.rhythm.accents)
            + f" :: dynamic={','.join(self.rhythm.dynamic_tempi)}"
        )
        rendered = self.lines + [diagnostic_line]
        if self.summary:
            summary_line = (
                "[summary] "
                f"voice_diversity={self.summary.voice_diversity:.2f}; "
                f"accent_focus={self.summary.accent_focus:.2f}; "
                f"dominant={self.summary.dominant_voice or '-'}; "
                f"fragments={self.summary.fragment_coverage}"
            )
            rendered.append(summary_line)
        rendered.append(rhythm_line)
        return rendered

    def to_dict(self) -> Dict[str, object]:
        """Convert the loop result into a serialisable structure."""

        return {
            "lines": list(self.lines),
            "diagnostics": self.diagnostics.as_dict(),
            "rhythm": {
                "tempo": self.rhythm.tempo,
                "pulses": self.rhythm.pulses,
                "accents": list(self.rhythm.accents),
                "dynamic_tempi": list(self.rhythm.dynamic_tempi),
            },
            "timeline": list(self.timeline),
            "summary": self.summary.as_dict() if self.summary else None,
        }


def summarize_loop(loop_result: LoopResult) -> LoopSummary:
    """Compute derived insights about a generated loop."""

    total_voices = len(VOICE_LIBRARY)
    used_voice_count = len(loop_result.diagnostics.voices)
    voice_diversity = used_voice_count / total_voices if total_voices else 0.0
    accents = loop_result.diagnostics.accents
    accent_focus = sum(accents) / len(accents) if accents else 0.0
    fragments_used = len(loop_result.diagnostics.fragments)
    dominant_voice: str | None = None
    if loop_result.diagnostics.voices:
        dominant_voice = loop_result.diagnostics.voices.most_common(1)[0][0]

    return LoopSummary(
        voice_diversity=voice_diversity,
        accent_focus=accent_focus,
        dominant_voice=dominant_voice,
        fragment_coverage=fragments_used,
    )


def load_fragments_from_file(path: str | Path) -> List[str]:
    """Load textual fragments from a newline-delimited file.

    Empty lines and comments (``#`` prefix) are ignored.
    """

    file_path = Path(path)
    contents = file_path.read_text(encoding="utf-8")
    fragments: List[str] = []
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fragments.append(line)
    return fragments


def _choose_voice(
    random_state: random.Random,
    *,
    previous: str | None = None,
    bias_map: Dict[str, float] | None = None,
) -> str:
    """Pick a narrative voice for a line in the loop."""

    pool = [voice for voice in VOICE_LIBRARY if voice != previous] or VOICE_LIBRARY
    if not bias_map:
        return random_state.choice(pool)

    weights = [bias_map.get(voice, 1.0) for voice in pool]
    if sum(weights) == 0:
        weights = [1.0] * len(pool)
    return random_state.choices(pool, weights=weights, k=1)[0]


def _build_rhythm(seed: LoopSeed, random_state: random.Random) -> LoopRhythm:
    """Construct a rhythmic pattern for the generated loop."""

    base_patterns: Dict[str, List[int]] = {
        "andante": [1, 0, 1, 0],
        "allegro": [1, 1, 0, 1],
        "largo": [1, 0, 0, 0],
        "adagio": [1, 0, 1, 1],
    }
    accents = base_patterns.get(seed.tempo, [1, 0, 1])
    # Rotate the pattern based on a random offset to avoid repeated openings.
    offset = random_state.randrange(len(accents)) if accents else 0
    accents = accents[offset:] + accents[:offset]

    tempi_variants = {
        "andante": ["steady", "gentle", "steady"],
        "allegro": ["quick", "bright", "quick"],
        "largo": ["expansive", "wide", "slow"],
        "adagio": ["calm", "reflective", "lingering"],
    }
    dynamic_tempi = tempi_variants.get(seed.tempo, [seed.tempo, "open", seed.tempo])
    return LoopRhythm(tempo=seed.tempo, pulses=seed.pulses, accents=accents, dynamic_tempi=dynamic_tempi)


def _render_line(
    seed: LoopSeed,
    random_state: random.Random,
    rhythm: LoopRhythm,
    index: int,
    *,
    previous_voice: str | None,
) -> Tuple[str, str, str | None, int, str, str]:
    """Build a single statement within the loop."""

    fragment = random_state.choice(seed.fragments) if seed.fragments else None
    voice = _choose_voice(
        random_state,
        previous=previous_voice,
        bias_map=seed.voice_bias,
    )

    gestures = {
        "observer": ["notes", "catalogues", "celebrates"],
        "cartographer": ["maps", "sketches", "traces"],
        "chorus": ["sings", "echoes", "harmonizes"],
        "wanderer": ["follows", "collects", "listens for"],
        "signal": ["transmits", "glows for", "amplifies"],
        "dream": ["imagines", "paints", "unfolds"],
    }

    gesture = random_state.choice(gestures[voice])
    subject = fragment or seed.motif
    accent = rhythm.accent_for(index)
    adverb_choices = {
        0: ["gently", "softly", "patiently"],
        1: ["brightly", "boldly", "intently"],
    }
    tempo_hint = random_state.choice(adverb_choices.get(accent, ["brightly"]))
    texture = rhythm.tempo_for(index)

    line = "".join(
        [
            f"The {voice} {gesture} the {subject} {tempo_hint},",
            f" keeping the {texture} cadence {('steady' if accent else 'open')}.",
        ]
    )
    return line, voice, fragment, accent, tempo_hint, texture


def generate_loop(seed: LoopSeed) -> LoopResult:
    """Generate the lines for a creative loop."""

    random_state = random.Random(seed.seed)
    rhythm = _build_rhythm(seed, random_state)
    diagnostics = LoopDiagnostics()

    lines: List[str] = []
    timeline: List[Dict[str, object]] = []
    previous_voice: str | None = None
    for index in range(seed.pulses):
        line, voice, fragment, accent, tempo_hint, texture = _render_line(
            seed,
            random_state,
            rhythm,
            index,
            previous_voice=previous_voice,
        )
        diagnostics.register(voice, fragment, accent)
        lines.append(line)
        timeline_entry = {
            "index": index,
            "voice": voice,
            "fragment": fragment,
            "accent": accent,
            "tempo_hint": tempo_hint,
            "texture": texture,
            "line": line,
        }
        timeline.append(timeline_entry)
        previous_voice = voice

    loop_result = LoopResult(
        lines=lines,
        diagnostics=diagnostics,
        rhythm=rhythm,
        timeline=timeline,
    )
    loop_result.summary = summarize_loop(loop_result)
    return loop_result


def _render_table(loop_result: LoopResult) -> str:
    """Render the loop timeline as a simple ASCII table."""

    headers = ["#", "voice", "fragment", "accent", "tempo", "texture", "line"]
    rows = [
        [
            str(entry["index"] + 1),
            entry["voice"],
            entry["fragment"] or "-",
            str(entry["accent"]),
            entry["tempo_hint"],
            entry["texture"],
            entry["line"],
        ]
        for entry in loop_result.timeline
    ]
    columns = list(zip(headers, *rows)) if rows else [(header,) for header in headers]
    widths = [max(len(cell) for cell in column) for column in columns]

    def _format_row(row: List[str]) -> str:
        padded = [cell.ljust(width) for cell, width in zip(row, widths)]
        return " | ".join(padded)

    divider = "-+-".join("-" * width for width in widths)
    rendered_rows = [_format_row(headers), divider]
    rendered_rows.extend(_format_row(row) for row in rows)
    return "\n".join(rendered_rows)


def compose_loop(
    seed: LoopSeed,
    *,
    format: str = "text",
    loop_result: LoopResult | None = None,
) -> str:
    """Create a creative loop in the requested output format.

    Supported formats are ``"text"``, ``"json"``, ``"markdown"``, and ``"table"``.
    """

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"Loop for '{seed.motif}' at {timestamp} ({seed.tempo})"
    loop_result = loop_result or generate_loop(seed)

    if format == "text":
        body = "\n".join(loop_result.render())
        return "\n".join([header, "", body])

    if format == "json":
        payload = {
            "motif": seed.motif,
            "tempo": seed.tempo,
            "pulses": seed.pulses,
            "timestamp": timestamp,
            "loop": loop_result.to_dict(),
        }
        return json.dumps(payload, indent=2)

    if format == "markdown":
        markdown_header = f"## Loop for '{seed.motif}'"
        metadata_line = (
            f"*Composed {timestamp} · Tempo: {seed.tempo} · Pulses: {seed.pulses}*"
        )
        bullet_lines = "\n".join(f"- {line}" for line in loop_result.lines)
        diagnostics_line = f"> Diagnostics: {loop_result.diagnostics.render_report()}"
        rhythm = loop_result.rhythm
        rhythm_line = (
            "> Rhythm: "
            f"tempo={rhythm.tempo}; pulses={rhythm.pulses}; "
            f"accents={','.join(str(value) for value in rhythm.accents)}; "
            f"dynamic={','.join(rhythm.dynamic_tempi)}"
        )
        summary_line = None
        if loop_result.summary:
            summary_line = (
                "> Summary: "
                f"diversity={loop_result.summary.voice_diversity:.2f}; "
                f"accent_focus={loop_result.summary.accent_focus:.2f}; "
                f"dominant={loop_result.summary.dominant_voice or '-'}; "
                f"fragments={loop_result.summary.fragment_coverage}"
            )
        return "\n".join(
            [
                markdown_header,
                metadata_line,
                "",
                bullet_lines,
                "",
                diagnostics_line,
                summary_line or "> Summary: unavailable",
                rhythm_line,
            ]
        )

    if format == "table":
        table_body = _render_table(loop_result)
        return "\n".join([header, "", table_body])

    raise ValueError("Unsupported format; expected 'text', 'json', 'markdown', or 'table'.")


def export_loop_result(
    path: str | Path,
    loop_result: LoopResult,
    seed: LoopSeed,
    *,
    format: str = "json",
) -> Path:
    """Persist a loop result to disk in the requested format."""

    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "json":
        payload = {
            "motif": seed.motif,
            "tempo": seed.tempo,
            "pulses": seed.pulses,
            "loop": loop_result.to_dict(),
        }
        export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return export_path

    if format == "markdown":
        markdown = compose_loop(seed, format="markdown", loop_result=loop_result)
        export_path.write_text(markdown + "\n", encoding="utf-8")
        return export_path

    raise ValueError("Unsupported export format; use 'json' or 'markdown'.")


def demo(
    motif: str,
    *fragments: str,
    tempo: str = "andante",
    pulses: int = 3,
    seed: int | None = None,
    format: str = "text",
) -> str:
    """Convenience wrapper for quickly generating a loop."""

    loop_seed = LoopSeed(
        motif=motif,
        fragments=fragments,
        tempo=tempo,
        pulses=pulses,
        seed=seed,
    )
    return compose_loop(loop_seed, format=format)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compose a short creative loop.")
    parser.add_argument("motif", help="Primary motif for the loop")
    parser.add_argument(
        "-f",
        "--fragment",
        dest="fragments",
        action="append",
        default=[],
        help="Optional fragment to weave into the loop",
    )
    parser.add_argument(
        "-F",
        "--fragments-file",
        dest="fragments_file",
        help="Path to a newline-delimited fragments file",
    )
    parser.add_argument(
        "-t",
        "--tempo",
        default="andante",
        help="Tempo hint to include in the header",
    )
    parser.add_argument(
        "-p",
        "--pulses",
        type=int,
        default=3,
        help="Number of statements to generate",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic output",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "table"],
        default="text",
        help="Choose between human-readable text, JSON, Markdown, or table output",
    )
    parser.add_argument(
        "--voice-bias",
        action="append",
        default=[],
        metavar="VOICE=WEIGHT",
        help="Weight a specific narrative voice (e.g., signal=3.5)",
    )
    parser.add_argument(
        "--export",
        help="Optional path to persist the generated loop",
    )
    parser.add_argument(
        "--export-format",
        choices=["json", "markdown"],
        default="json",
        help="Format to use when exporting the loop",
    )

    args = parser.parse_args()
    fragments = list(args.fragments)
    if args.fragments_file:
        try:
            fragments.extend(load_fragments_from_file(args.fragments_file))
        except OSError as exc:
            parser.error(f"Unable to load fragments from {args.fragments_file}: {exc}")
    voice_bias: Dict[str, float] = {}
    for entry in args.voice_bias:
        if "=" not in entry:
            parser.error("Voice bias must use VOICE=WEIGHT format")
        voice, weight_text = entry.split("=", 1)
        try:
            voice_bias[voice.strip()] = float(weight_text)
        except ValueError:
            parser.error(f"Invalid weight for voice '{voice}': {weight_text}")
    seed = LoopSeed(
        motif=args.motif,
        fragments=fragments,
        tempo=args.tempo,
        pulses=args.pulses,
        seed=args.seed,
        voice_bias=voice_bias,
    )
    loop_result = generate_loop(seed)
    print(compose_loop(seed, format=args.format, loop_result=loop_result))
    if args.export:
        try:
            export_loop_result(args.export, loop_result, seed, format=args.export_format)
            print(f"[saved] Exported loop to {args.export} ({args.export_format})")
        except ValueError as exc:
            parser.error(str(exc))
