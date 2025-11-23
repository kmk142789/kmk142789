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
import html
import io
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import random
from statistics import fmean, mean
from typing import Dict, Iterable, List, Mapping, Tuple


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


def load_voice_bias_profile(path: str | Path) -> Dict[str, float]:
    """Load a narrative voice weighting profile from disk."""

    profile_path = Path(path)
    contents = profile_path.read_text(encoding="utf-8")
    try:
        data = json.loads(contents)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Voice bias file is not valid JSON: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ValueError("Voice bias file must define an object mapping voices to weights")
    bias: Dict[str, float] = {}
    for voice, raw_weight in data.items():
        if voice not in VOICE_LIBRARY:
            continue
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            continue
        if weight <= 0:
            continue
        bias[voice] = weight
    return bias


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
    timestamp: str | None = None,
) -> str:
    """Create a creative loop in the requested output format.

    Supported formats are ``"text"``, ``"json"``, ``"markdown"``, ``"table"``,
    ``"csv"``, ``"summary"``, ``"insights"``, and ``"html"``.
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

    if format == "insights":
        summary = loop_result.summary or summarize_loop(loop_result)
        diagnostics_line = loop_result.diagnostics.render_report()
        voice_rankings = loop_result.diagnostics.voices.most_common()
        fragment_rankings = loop_result.diagnostics.fragments.most_common(3)
        voice_text = ", ".join(f"{voice}×{count}" for voice, count in voice_rankings) or "none"
        fragment_text = ", ".join(
            f"{fragment}×{count}" for fragment, count in fragment_rankings
        ) or "none"
        lines = [
            f"Insights for '{seed.motif}'",
            "",
            f"tempo={seed.tempo} | pulses={seed.pulses} | generated={timestamp}",
            "",
            "Primary metrics:",
            f"- voice diversity: {summary.voice_diversity:.2f}",
            f"- accent focus: {summary.accent_focus:.2f}",
            f"- fragment coverage: {summary.fragment_coverage}",
            f"- dominant voice: {summary.dominant_voice or 'none'}",
            f"- voices engaged: {voice_text}",
            f"- top fragments: {fragment_text}",
            f"- diagnostics: {diagnostics_line}",
            "",
            "Moments:",
        ]
        for entry in loop_result.timeline:
            lines.append(
                (
                    f"  {entry['index'] + 1}. {entry['voice']} accent={entry['accent']} "
                    f"({entry['tempo_hint']}/{entry['texture']}): {entry['line']}"
                )
            )
        return "\n".join(lines)

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

    if format == "summary":
        summary = loop_result.summary or summarize_loop(loop_result)
        diagnostics_line = loop_result.diagnostics.render_report()
        rhythm = loop_result.rhythm
        lines = [
            header,
            "",
            f"Voice diversity: {summary.voice_diversity:.2f}",
            f"Accent focus: {summary.accent_focus:.2f}",
            f"Dominant voice: {summary.dominant_voice or '-'}",
            f"Fragments highlighted: {summary.fragment_coverage}",
            f"Lines composed: {len(loop_result.lines)}",
            f"Rhythm accents: {','.join(str(value) for value in rhythm.accents)}",
            f"Rhythm dynamics: {','.join(rhythm.dynamic_tempi)}",
            f"Diagnostics: {diagnostics_line}",
        ]
        return "\n".join(lines)

    if format == "html":
        summary = loop_result.summary or summarize_loop(loop_result)
        diagnostics_text = html.escape(loop_result.diagnostics.render_report())
        rhythm = loop_result.rhythm
        lines = "\n".join(f"<li>{html.escape(line)}</li>" for line in loop_result.lines)
        summary_items = "\n".join(
            [
                f"<li><strong>Voice diversity:</strong> {summary.voice_diversity:.2f}</li>",
                f"<li><strong>Accent focus:</strong> {summary.accent_focus:.2f}</li>",
                f"<li><strong>Dominant voice:</strong> {html.escape(summary.dominant_voice or '-')}</li>",
                f"<li><strong>Fragments highlighted:</strong> {summary.fragment_coverage}</li>",
                f"<li><strong>Rhythm accents:</strong> {','.join(str(value) for value in rhythm.accents)}</li>",
                f"<li><strong>Rhythm dynamics:</strong> {','.join(html.escape(value) for value in rhythm.dynamic_tempi)}</li>",
                f"<li><strong>Diagnostics:</strong> {diagnostics_text}</li>",
            ]
        )
        timeline_rows = "\n".join(
            (
                "<tr>"
                f"<td>{entry['index'] + 1}</td>"
                f"<td>{html.escape(entry['voice'])}</td>"
                f"<td>{html.escape(entry['fragment'] or '-')}</td>"
                f"<td>{entry['accent']}</td>"
                f"<td>{html.escape(entry['tempo_hint'])}</td>"
                f"<td>{html.escape(entry['texture'])}</td>"
                f"<td>{html.escape(entry['line'])}</td>"
                "</tr>"
            )
            for entry in loop_result.timeline
        )
        return "\n".join(
            [
                "<!DOCTYPE html>",
                "<html lang=\"en\">",
                "<head>",
                "  <meta charset=\"utf-8\" />",
                f"  <title>Loop for {html.escape(seed.motif)}</title>",
                "  <style>",
                "    body { font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; padding: 1.5rem; color: #0c1021; }",
                "    h2 { margin-top: 0; }",
                "    ul { padding-left: 1.25rem; }",
                "    .meta { color: #555; margin-bottom: 0.5rem; }",
                "    .summary { background: #f5f5fa; border: 1px solid #e0e0ee; padding: 0.75rem; border-radius: 8px; }",
                "    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }",
                "    th, td { border: 1px solid #d4d7df; padding: 0.5rem; text-align: left; }",
                "    th { background: #f0f2f8; }",
                "  </style>",
                "</head>",
                "<body>",
                f"  <h2>Loop for '{html.escape(seed.motif)}'</h2>",
                f"  <p class=\"meta\">Composed {html.escape(timestamp)} · Tempo: {html.escape(seed.tempo)} · Pulses: {seed.pulses}</p>",
                "  <ul>",
                f"    {lines}",
                "  </ul>",
                "  <div class=\"summary\">",
                "    <strong>Summary</strong>",
                "    <ul>",
                f"      {summary_items}",
                "    </ul>",
                "  </div>",
                "  <table>",
                "    <thead>",
                "      <tr><th>#</th><th>Voice</th><th>Fragment</th><th>Accent</th><th>Tempo</th><th>Texture</th><th>Line</th></tr>",
                "    </thead>",
                "    <tbody>",
                f"      {timeline_rows}",
                "    </tbody>",
                "  </table>",
                "</body>",
                "</html>",
            ]
        )

    raise ValueError(
        "Unsupported format; expected 'text', 'json', 'markdown', 'table', 'csv', 'summary', 'insights', or 'html'."
    )


def _extension_for_format(output_format: str) -> str:
    mapping = {
        "text": "txt",
        "json": "json",
        "markdown": "md",
        "table": "txt",
        "csv": "csv",
        "summary": "txt",
        "insights": "txt",
        "html": "html",
    }
    return mapping.get(output_format, "txt")


def summarise_loop_suite(loop_results: Iterable[LoopResult]) -> Dict[str, object]:
    """Aggregate diagnostics across multiple loop results."""

    results = list(loop_results)
    voice_counts: Counter[str] = Counter()
    fragment_counts: Counter[str] = Counter()
    accent_values: List[int] = []
    tempo_counts: Counter[str] = Counter()
    dominant_voice_counts: Counter[str] = Counter()
    voice_diversities: List[float] = []
    fragment_coverages: List[int] = []
    total_lines = 0

    for result in results:
        voice_counts.update(result.diagnostics.voices)
        fragment_counts.update(result.diagnostics.fragments)
        accent_values.extend(result.diagnostics.accents)
        tempo_counts[result.rhythm.tempo] += 1
        total_lines += len(result.lines)
        summary = result.summary or summarize_loop(result)
        voice_diversities.append(summary.voice_diversity)
        fragment_coverages.append(summary.fragment_coverage)
        if summary.dominant_voice:
            dominant_voice_counts[summary.dominant_voice] += 1

    average_accent = mean(accent_values) if accent_values else 0.0
    mean_voice_diversity = fmean(voice_diversities) if voice_diversities else 0.0
    mean_fragment_coverage = (
        fmean(fragment_coverages) if fragment_coverages else 0.0
    )
    summary = {
        "total_loops": len(results),
        "total_lines": total_lines,
        "unique_voices": len(voice_counts),
        "unique_fragments": len(fragment_counts),
        "top_voices": voice_counts.most_common(3),
        "top_fragments": fragment_counts.most_common(3),
        "tempo_distribution": dict(tempo_counts),
        "average_accent_intensity": average_accent,
        "mean_voice_diversity": mean_voice_diversity,
        "mean_fragment_coverage": mean_fragment_coverage,
        "dominant_voice_distribution": dominant_voice_counts.most_common(),
    }
    return summary


def export_suite_summary(summary: Mapping[str, object], path: str | Path) -> Path:
    """Persist aggregated suite diagnostics as JSON."""

    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return export_path


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
    lines.append(
        f"- mean voice diversity: {summary.get('mean_voice_diversity', 0.0):.2f}"
    )
    lines.append(
        f"- mean fragment coverage: {summary.get('mean_fragment_coverage', 0.0):.2f}"
    )
    lines.append(
        "- dominant voice distribution: "
        + _format_pairs(summary.get('dominant_voice_distribution', []))
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
        choices=["text", "json", "markdown", "table", "csv", "summary", "insights", "html"],
        default="text",
        help=(
            "Choose between human-readable text, JSON, Markdown, table, CSV, summary, "
            "insights, or HTML output"
        ),
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
    parser.add_argument(
        "--summary-output",
        type=Path,
        dest="summary_output",
        help="Optional path to store aggregated summary diagnostics as JSON",
    )
    parser.add_argument(
        "--voice-bias",
        action="append",
        default=[],
        metavar="VOICE=WEIGHT",
        help="Weight a specific narrative voice (e.g., signal=3.5)",
    )
    parser.add_argument(
        "--voice-bias-file",
        type=Path,
        dest="voice_bias_file",
        help="Optional JSON file describing additional voice weights",
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
    if args.voice_bias_file:
        try:
            voice_bias.update(load_voice_bias_profile(args.voice_bias_file))
        except (OSError, ValueError) as exc:
            parser.error(f"Unable to load voice bias profile: {exc}")
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

    suite_summary = summarise_loop_suite(package.result for package in packages)
    if args.variations > 1:
        print(format_suite_summary(suite_summary))
    if args.summary_output:
        try:
            export_suite_summary(suite_summary, args.summary_output)
            print(f"[saved] Suite summary exported to {args.summary_output}")
        except OSError as exc:
            parser.error(f"Unable to export suite summary: {exc}")

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
