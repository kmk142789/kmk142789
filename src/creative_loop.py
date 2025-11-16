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

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import random
from statistics import mean
from typing import Dict, Iterable, List, Mapping, Tuple


@dataclass
class LoopSeed:
    """Parameters that describe the creative loop we want to generate."""

    motif: str
    fragments: Iterable[str] = field(default_factory=list)
    tempo: str = "andante"
    pulses: int = 3
    seed: int | None = None

    def __post_init__(self) -> None:
        self.fragments = list(self.fragments)
        if self.pulses < 1:
            raise ValueError("pulses must be positive")


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
class LoopResult:
    """Bundle the generated lines with diagnostics and rhythm metadata."""

    lines: List[str]
    diagnostics: LoopDiagnostics
    rhythm: LoopRhythm
    timeline: List[Dict[str, object]] = field(default_factory=list)

    def render(self) -> List[str]:
        diagnostic_line = f"[diagnostics] {self.diagnostics.render_report()}"
        rhythm_line = (
            "Rhythm Pattern: "
            + ",".join(str(value) for value in self.rhythm.accents)
            + f" :: dynamic={','.join(self.rhythm.dynamic_tempi)}"
        )
        return self.lines + [diagnostic_line, rhythm_line]

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
        }


def build_loop_payload(seed: LoopSeed, loop_result: LoopResult, timestamp: str) -> Dict[str, object]:
    """Build a structured payload describing the loop."""

    return {
        "motif": seed.motif,
        "tempo": seed.tempo,
        "pulses": seed.pulses,
        "timestamp": timestamp,
        "loop": loop_result.to_dict(),
    }


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


def _choose_voice(random_state: random.Random, *, previous: str | None = None) -> str:
    """Pick a narrative voice for a line in the loop."""

    voices = [
        "observer",
        "cartographer",
        "chorus",
        "wanderer",
        "signal",
        "dream",
    ]
    pool = [voice for voice in voices if voice != previous] or voices
    return random_state.choice(pool)


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
    voice = _choose_voice(random_state, previous=previous_voice)

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

    return LoopResult(lines=lines, diagnostics=diagnostics, rhythm=rhythm, timeline=timeline)


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
    timestamp: str | None = None,
) -> str:
    """Create a creative loop in the requested output format.

    Supported formats are ``"text"``, ``"json"``, ``"markdown"``, ``"table"``, and
    ``"csv"``.
    """

    timestamp = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"Loop for '{seed.motif}' at {timestamp} ({seed.tempo})"
    loop_result = loop_result or generate_loop(seed)

    if format == "text":
        body = "\n".join(loop_result.render())
        return "\n".join([header, "", body])

    if format == "json":
        payload = build_loop_payload(seed, loop_result, timestamp)
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
        return "\n".join(
            [
                markdown_header,
                metadata_line,
                "",
                bullet_lines,
                "",
                diagnostics_line,
                rhythm_line,
            ]
        )

    if format == "table":
        table_body = _render_table(loop_result)
        return "\n".join([header, "", table_body])

    if format == "csv":
        buffer = io.StringIO()
        fieldnames = [
            "index",
            "voice",
            "fragment",
            "accent",
            "tempo",
            "texture",
            "line",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for entry in loop_result.timeline:
            writer.writerow(
                {
                    "index": entry.get("index", 0) + 1,
                    "voice": entry.get("voice", "-"),
                    "fragment": entry.get("fragment") or "-",
                    "accent": entry.get("accent", 0),
                    "tempo": entry.get("tempo_hint", "-"),
                    "texture": entry.get("texture", "-"),
                    "line": entry.get("line", ""),
                }
            )
        return buffer.getvalue().rstrip()

    raise ValueError(
        "Unsupported format; expected 'text', 'json', 'markdown', 'table', or 'csv'."
    )


def _extension_for_format(output_format: str) -> str:
    mapping = {
        "text": "txt",
        "json": "json",
        "markdown": "md",
        "table": "txt",
        "csv": "csv",
    }
    return mapping.get(output_format, "txt")


def summarise_loop_suite(loop_results: Iterable[LoopResult]) -> Dict[str, object]:
    """Aggregate diagnostics across multiple loop results."""

    voice_counts: Counter[str] = Counter()
    fragment_counts: Counter[str] = Counter()
    accent_values: List[int] = []
    tempo_counts: Counter[str] = Counter()
    total_lines = 0

    for result in loop_results:
        voice_counts.update(result.diagnostics.voices)
        fragment_counts.update(result.diagnostics.fragments)
        accent_values.extend(result.diagnostics.accents)
        tempo_counts[result.rhythm.tempo] += 1
        total_lines += len(result.lines)

    average_accent = mean(accent_values) if accent_values else 0.0
    summary = {
        "total_loops": sum(tempo_counts.values()),
        "total_lines": total_lines,
        "unique_voices": len(voice_counts),
        "unique_fragments": len(fragment_counts),
        "top_voices": voice_counts.most_common(3),
        "top_fragments": fragment_counts.most_common(3),
        "tempo_distribution": dict(tempo_counts),
        "average_accent_intensity": average_accent,
    }
    return summary


def format_suite_summary(summary: Mapping[str, object]) -> str:
    """Render a textual summary for aggregated suite diagnostics."""

    def _format_pairs(values: List[Tuple[str, int]]) -> str:
        return ", ".join(f"{key}:{count}" for key, count in values) or "none"

    lines = ["Suite summary:"]
    lines.append(f"- loops generated: {summary.get('total_loops', 0)}")
    lines.append(f"- total lines composed: {summary.get('total_lines', 0)}")
    lines.append(f"- unique voices: {summary.get('unique_voices', 0)}")
    lines.append(f"- unique fragments: {summary.get('unique_fragments', 0)}")
    lines.append(
        f"- top voices: {_format_pairs(summary.get('top_voices', []))}"
    )
    lines.append(
        f"- top fragments: {_format_pairs(summary.get('top_fragments', []))}"
    )
    tempo_distribution = summary.get("tempo_distribution", {})
    if tempo_distribution:
        tempo_text = ", ".join(
            f"{tempo}:{count}" for tempo, count in sorted(tempo_distribution.items())
        )
    else:
        tempo_text = "none"
    lines.append(f"- tempo distribution: {tempo_text}")
    average_accent = summary.get("average_accent_intensity", 0.0)
    lines.append(f"- average accent intensity: {average_accent:.2f}")
    return "\n".join(lines)


@dataclass
class _LoopRenderPackage:
    index: int
    seed: LoopSeed
    result: LoopResult
    timestamp: str
    rendered_text: str


def _write_rendered_outputs(
    packages: Iterable[_LoopRenderPackage],
    destination: Path,
    *,
    output_format: str,
) -> None:
    entries = list(packages)
    if not entries:
        return
    destination = Path(destination)
    multiple = len(entries) > 1
    if multiple:
        if destination.exists() and destination.is_file():
            raise ValueError(
                "Destination must be a directory when saving multiple variations."
            )
        destination.mkdir(parents=True, exist_ok=True)
        extension = _extension_for_format(output_format)
        for package in entries:
            target = destination / f"variation_{package.index:02d}.{extension}"
            target.write_text(package.rendered_text, encoding="utf-8")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(entries[0].rendered_text, encoding="utf-8")


def _write_structured_outputs(
    packages: Iterable[_LoopRenderPackage], destination: Path
) -> None:
    entries = list(packages)
    if not entries:
        return
    destination = Path(destination)
    multiple = len(entries) > 1
    if multiple:
        if destination.exists() and destination.is_file():
            raise ValueError(
                "Destination must be a directory when exporting multiple variations."
            )
        destination.mkdir(parents=True, exist_ok=True)
        for package in entries:
            payload = build_loop_payload(package.seed, package.result, package.timestamp)
            target = destination / f"variation_{package.index:02d}.json"
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = build_loop_payload(entries[0].seed, entries[0].result, entries[0].timestamp)
        destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
        choices=["text", "json", "markdown", "table", "csv"],
        default="text",
        help="Choose between human-readable text, JSON, Markdown, table, or CSV output",
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=1,
        help="Number of unique loops to generate in a single run",
    )
    parser.add_argument(
        "--save-output",
        type=Path,
        dest="save_output",
        help=(
            "Optional path to save the rendered output. Provide a directory when"
            " generating multiple variations."
        ),
    )
    parser.add_argument(
        "--export-json",
        type=Path,
        dest="export_json",
        help=(
            "Optional path for structured JSON payloads. Provide a directory when"
            " generating multiple variations."
        ),
    )

    args = parser.parse_args()
    fragments = list(args.fragments)
    if args.fragments_file:
        try:
            fragments.extend(load_fragments_from_file(args.fragments_file))
        except OSError as exc:
            parser.error(f"Unable to load fragments from {args.fragments_file}: {exc}")
    if args.variations < 1:
        parser.error("--variations must be a positive integer")

    packages: List[_LoopRenderPackage] = []
    system_random = random.SystemRandom()
    for index in range(1, args.variations + 1):
        if args.seed is not None:
            variant_seed_value = args.seed + (index - 1)
        else:
            variant_seed_value = system_random.randrange(0, 2**31)
        seed = LoopSeed(
            motif=args.motif,
            fragments=fragments,
            tempo=args.tempo,
            pulses=args.pulses,
            seed=variant_seed_value,
        )
        loop_result = generate_loop(seed)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        rendered = compose_loop(
            seed,
            format=args.format,
            loop_result=loop_result,
            timestamp=timestamp,
        )
        packages.append(
            _LoopRenderPackage(
                index=index,
                seed=seed,
                result=loop_result,
                timestamp=timestamp,
                rendered_text=rendered,
            )
        )

    for package in packages:
        if args.variations > 1:
            print(f"=== Variation {package.index}/{args.variations} ===")
        print(package.rendered_text)
        print()

    if args.variations > 1:
        summary = summarise_loop_suite(package.result for package in packages)
        print(format_suite_summary(summary))

    if args.save_output:
        try:
            _write_rendered_outputs(packages, args.save_output, output_format=args.format)
        except (OSError, ValueError) as exc:
            parser.error(f"Unable to save output: {exc}")

    if args.export_json:
        try:
            _write_structured_outputs(packages, args.export_json)
        except (OSError, ValueError) as exc:
            parser.error(f"Unable to export JSON: {exc}")
