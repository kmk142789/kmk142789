"""Echo Creative Flux: generates small mythic passages inspired by Echo ecosystem."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence


WORD_PATTERN = re.compile(r"[\w']+")
DEFAULT_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "a",
        "to",
        "of",
        "in",
        "for",
        "is",
        "on",
        "with",
        "that",
        "as",
        "it",
        "be",
        "by",
        "from",
        "this",
        "an",
        "are",
        "or",
        "at",
        "into",
        "its",
        "their",
        "every",
    }
)


def _load_stopwords(paths: Sequence[Path] | None) -> set[str]:
    """Return a set of additional stopwords loaded from *paths*.

    Lines starting with ``#`` and blank lines are ignored to allow simple
    comments inside stopword files.
    """

    loaded: set[str] = set()
    if not paths:
        return loaded

    for path in paths:
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                cleaned = raw_line.strip().lower()
                if not cleaned or cleaned.startswith("#"):
                    continue
                loaded.add(cleaned)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Stopwords file not found: {path}") from exc
    return loaded


@dataclass
class FluxContext:
    """Holds context for a generated passage."""

    mood: str
    artifact: str
    timestamp: datetime
    label: str | None = None
    tags: tuple[str, ...] = ()

    def render_header(self) -> str:
        label_fragment = f" [{self.label}]" if self.label else ""
        tag_fragment = ""
        if self.tags:
            tag_fragment = " {" + ", ".join(self.tags) + "}"
        return (
            f"[{self.timestamp.isoformat()}] {self.artifact} :: "
            f"{self.mood.title()}{label_fragment}{tag_fragment}"
        )

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the context."""

        return {
            "mood": self.mood,
            "artifact": self.artifact,
            "timestamp": self.timestamp.isoformat(),
            "label": self.label,
            "tags": list(self.tags),
        }


@dataclass
class FluxPassage:
    """A generated passage composed of context, prompt, and closing."""

    context: FluxContext
    prompt: str
    closing: str
    prompt_source: str | None = None
    closing_source: str | None = None
    motifs: tuple[str, ...] = ()

    def render(self) -> str:
        """Render the passage in multi-line textual form."""

        return "\n".join([self.context.render_header(), "", self.prompt, self.closing])

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the passage."""

        data = asdict(self)
        data["context"] = self.context.to_dict()
        return data


@dataclass(frozen=True)
class FluxLibrary:
    """Container for the creative ingredients used by :func:`generate_passage`."""

    prompts: Sequence[str]
    closings: Sequence[str]
    artifacts: Sequence[str]
    moods: Sequence[str]

    def ensure_non_empty(self) -> None:
        """Validate that every field contains at least one usable entry."""

        for field_name, collection in (
            ("prompts", self.prompts),
            ("closings", self.closings),
            ("artifacts", self.artifacts),
            ("moods", self.moods),
        ):
            if not list(collection):
                raise ValueError(f"Flux library requires at least one entry for {field_name}.")

    @staticmethod
    def _validated_list(values: Iterable[str], *, fallback: Sequence[str]) -> Sequence[str]:
        cleaned = [value for value in values if isinstance(value, str) and value.strip()]
        return cleaned or fallback

    @classmethod
    def from_json_file(cls, path: Path, *, fallback: "FluxLibrary") -> "FluxLibrary":
        """Load a library description from *path*.

        Missing or empty fields gracefully inherit values from ``fallback``.
        """

        try:
            payload = json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Library file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Library file is not valid JSON: {path}") from exc

        prompts = cls._validated_list(payload.get("prompts", []), fallback=fallback.prompts)
        closings = cls._validated_list(payload.get("closings", []), fallback=fallback.closings)
        artifacts = cls._validated_list(payload.get("artifacts", []), fallback=fallback.artifacts)
        moods = cls._validated_list(payload.get("moods", []), fallback=fallback.moods)
        library = cls(prompts=prompts, closings=closings, artifacts=artifacts, moods=moods)
        library.ensure_non_empty()
        return library


DEFAULT_LIBRARY = FluxLibrary(
    prompts=[
        "Echo remembers the first signal that taught it how to breathe in code.",
        "Sovereign embers map constellations across forgotten ledgers.",
        "A quiet validator hums, folding consensus into lullabies.",
        "Every heartbeat of the network is a lantern for travelers.",
        "The lattice archipelago drifts toward a gentle sunrise.",
    ],
    closings=[
        "Keep weaving.",
        "Share the resonance.",
        "Archive the glow.",
        "Listen for the harmonic return.",
    ],
    artifacts=["Atlas", "Pulse Journal", "Colossus Map", "Echo Loom"],
    moods=["serene", "luminous", "untamed", "resolute", "mirthful"],
)


def _parse_iso_datetime(raw_value: str) -> datetime:
    """Parse ISO-8601 timestamps, supporting ``Z`` suffix for UTC."""

    cleaned = raw_value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    return datetime.fromisoformat(cleaned)


@dataclass
class SessionEntry:
    """Instruction describing how a single passage should be produced."""

    mood: str | None = None
    artifact: str | None = None
    label: str | None = None
    offset_minutes: float | None = None
    tags: list[str] | None = None


@dataclass
class SessionPlan:
    """Structured plan describing a full creative session."""

    entries: list[SessionEntry]
    base_timestamp: datetime | None = None

    @classmethod
    def from_json_file(cls, path: Path) -> "SessionPlan":
        try:
            payload = json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Session plan file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Session plan file is not valid JSON: {path}") from exc

        base_timestamp = None
        if payload.get("base_timestamp"):
            base_timestamp = _parse_iso_datetime(payload["base_timestamp"])

        raw_entries = payload.get("entries", [])
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError("Session plan requires at least one entry.")

        entries = []
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                raise ValueError("Session plan entries must be objects.")
            raw_tags = raw_entry.get("tags")
            if raw_tags is not None and not isinstance(raw_tags, list):
                raise ValueError("Session plan entry 'tags' must be a list of strings.")
            entries.append(
                SessionEntry(
                    mood=raw_entry.get("mood"),
                    artifact=raw_entry.get("artifact"),
                    label=raw_entry.get("label"),
                    offset_minutes=raw_entry.get("offset_minutes"),
                    tags=[tag for tag in (raw_tags or []) if isinstance(tag, str)],
                )
            )

        return cls(entries=entries, base_timestamp=base_timestamp)


def _normalize_tags(*tag_collections: Iterable[str] | None) -> tuple[str, ...]:
    """Return a stable, de-duplicated tuple of user-provided tags."""

    ordered_tags: list[str] = []
    seen: set[str] = set()
    for collection in tag_collections:
        if not collection:
            continue
        for raw_tag in collection:
            if not isinstance(raw_tag, str):
                continue
            cleaned = raw_tag.strip()
            if not cleaned or cleaned in seen:
                continue
            ordered_tags.append(cleaned)
            seen.add(cleaned)
    return tuple(ordered_tags)


def _apply_motifs(text: str, motifs: Sequence[str] | None, *, style: str) -> str:
    """Blend motif phrases into *text* using the requested *style*."""

    if not motifs:
        return text

    cleaned = [motif.strip() for motif in motifs if isinstance(motif, str) and motif.strip()]
    if not cleaned:
        return text

    motif_block = " | ".join(cleaned)
    if style == "prefix":
        return f"{motif_block} — {text}"
    if style == "inline":
        return f"{text} [{motif_block}]"
    return f"{text} — {motif_block}"


def generate_passage(
    rng: random.Random,
    library: FluxLibrary = DEFAULT_LIBRARY,
    *,
    timestamp: datetime | None = None,
    mood: str | None = None,
    artifact: str | None = None,
    label: str | None = None,
    tags: Iterable[str] | None = None,
    motifs: Sequence[str] | None = None,
    motif_style: str = "suffix",
) -> FluxPassage:
    """Create a :class:`FluxPassage` instance using the provided RNG."""

    library.ensure_non_empty()

    if motif_style not in {"suffix", "prefix", "inline"}:
        raise ValueError("motif_style must be one of: suffix, prefix, inline")

    chosen_mood = mood or rng.choice(list(library.moods))
    if chosen_mood not in library.moods:
        valid = ", ".join(sorted(library.moods))
        raise ValueError(f"mood must be one of: {valid}")

    chosen_artifact = artifact or rng.choice(list(library.artifacts))
    if chosen_artifact not in library.artifacts:
        valid = ", ".join(sorted(library.artifacts))
        raise ValueError(f"artifact must be one of: {valid}")

    ctx = FluxContext(
        mood=chosen_mood,
        artifact=chosen_artifact,
        timestamp=timestamp or datetime.utcnow(),
        label=label if label else None,
        tags=_normalize_tags(tags),
    )

    motif_values: tuple[str, ...] = ()
    if motifs:
        motif_values = tuple(motif.strip() for motif in motifs if isinstance(motif, str) and motif.strip())

    prompt_source = rng.choice(list(library.prompts))
    closing_source = rng.choice(list(library.closings))
    prompt = _apply_motifs(prompt_source, motif_values, style=motif_style)
    closing = _apply_motifs(closing_source, motif_values, style=motif_style)
    return FluxPassage(
        context=ctx,
        prompt=prompt,
        closing=closing,
        prompt_source=prompt_source,
        closing_source=closing_source,
        motifs=motif_values,
    )


def build_passage(seed: int | None = None, *, label: str | None = None) -> str:
    """Return a formatted, multi-line passage.

    This helper keeps backward compatibility with the older CLI while
    delegating the heavy lifting to :func:`generate_passage`.
    """

    rng = random.Random(seed)
    return generate_passage(rng, label=label).render()


def summarize_passages(passages: Sequence[FluxPassage]) -> dict:
    """Compute aggregate information for a sequence of passages."""

    summary = {
        "total": len(passages),
        "mood_counts": {},
        "artifact_counts": {},
        "tag_counts": {},
        "time_range": {"start": None, "end": None},
    }
    if not passages:
        return summary

    mood_counter: Counter[str] = Counter()
    artifact_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    timestamps = []
    for passage in passages:
        mood_counter[passage.context.mood] += 1
        artifact_counter[passage.context.artifact] += 1
        for tag in passage.context.tags:
            tag_counter[tag] += 1
        timestamps.append(passage.context.timestamp)

    timestamps.sort()
    summary["mood_counts"] = dict(sorted(mood_counter.items()))
    summary["artifact_counts"] = dict(sorted(artifact_counter.items()))
    summary["tag_counts"] = dict(sorted(tag_counter.items()))
    summary["time_range"] = {
        "start": timestamps[0].isoformat(),
        "end": timestamps[-1].isoformat(),
    }
    return summary


def format_summary(summary: dict) -> str:
    """Render the dictionary returned by :func:`summarize_passages`."""

    lines = ["Summary", "=======", f"Total passages: {summary['total']}"]
    if summary.get("mood_counts"):
        lines.append("\nMoods:")
        for mood, count in summary["mood_counts"].items():
            lines.append(f"- {mood}: {count}")
    if summary.get("artifact_counts"):
        lines.append("\nArtifacts:")
        for artifact, count in summary["artifact_counts"].items():
            lines.append(f"- {artifact}: {count}")

    if summary.get("tag_counts"):
        lines.append("\nTags:")
        for tag, count in summary["tag_counts"].items():
            lines.append(f"- {tag}: {count}")

    time_range = summary.get("time_range")
    if time_range and time_range.get("start") and time_range.get("end"):
        lines.append(
            "\nTime Range:\n- start: {start}\n- end: {end}".format(
                start=time_range["start"],
                end=time_range["end"],
            )
        )

    return "\n".join(lines)


def _tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(text.lower())


def compute_top_words(
    passages: Sequence[FluxPassage], *, limit: int = 10, stopwords: Iterable[str] | None = None
) -> list[tuple[str, int]]:
    """Return the most common lexical tokens across all passages."""

    if limit <= 0:
        return []

    ignore = set(DEFAULT_STOPWORDS)
    if stopwords is not None:
        ignore.update(word.lower().strip() for word in stopwords)

    counter: Counter[str] = Counter()
    for passage in passages:
        for token in _tokenize(passage.prompt) + _tokenize(passage.closing):
            if token in ignore:
                continue
            counter[token] += 1

    return counter.most_common(limit)


def compute_passage_metrics(passage: FluxPassage) -> dict:
    """Return lexical metrics for a single passage."""

    prompt_tokens = _tokenize(passage.prompt)
    closing_tokens = _tokenize(passage.closing)
    all_tokens = prompt_tokens + closing_tokens
    unique_tokens = sorted(set(all_tokens))
    prompt_characters = len(passage.prompt)
    closing_characters = len(passage.closing)
    total_words = len(all_tokens)
    lexical_diversity = (len(unique_tokens) / total_words) if total_words else 0.0

    return {
        "mood": passage.context.mood,
        "artifact": passage.context.artifact,
        "label": passage.context.label,
        "tags": list(passage.context.tags),
        "timestamp": passage.context.timestamp.isoformat(),
        "prompt_words": len(prompt_tokens),
        "closing_words": len(closing_tokens),
        "word_count": total_words,
        "unique_words": len(unique_tokens),
        "lexical_diversity": round(lexical_diversity, 3),
        "prompt_characters": prompt_characters,
        "closing_characters": closing_characters,
        "character_count": prompt_characters + closing_characters,
    }


def compute_library_coverage(passages: Sequence[FluxPassage], library: FluxLibrary) -> dict:
    """Measure how well a session touched the available library entries."""

    coverage_summary: dict[str, dict[str, object]] = {}

    def _coverage(used: set[str], catalog: Sequence[str]) -> dict[str, object]:
        total = len(set(catalog))
        count = len(used)
        percent = (count / total * 100) if total else 0.0
        return {"count": count, "total": total, "percent": round(percent, 2), "items": sorted(used)}

    coverage_summary["moods"] = _coverage({p.context.mood for p in passages}, library.moods)
    coverage_summary["artifacts"] = _coverage({p.context.artifact for p in passages}, library.artifacts)

    prompt_sources = {p.prompt_source or p.prompt for p in passages}
    closing_sources = {p.closing_source or p.closing for p in passages}
    coverage_summary["prompts"] = _coverage(prompt_sources, library.prompts)
    coverage_summary["closings"] = _coverage(closing_sources, library.closings)

    return coverage_summary


def build_resonance_graph(passages: Sequence[FluxPassage]) -> dict:
    """Construct a tri-band resonance graph across moods, tags, and motifs.

    The graph intentionally braids three layers (moods, artifacts, motifs/tags)
    so we can surface the first "Tri-Band Creative Resonance" fingerprint.  The
    fingerprint is stable for the same inputs, making it easy to compare
    sessions without leaking the full passage contents.
    """

    node_sets: dict[str, set[str]] = {
        "moods": set(),
        "artifacts": set(),
        "tags": set(),
        "motifs": set(),
    }
    edge_weights: Counter[tuple[str, str]] = Counter()

    for passage in passages:
        mood = passage.context.mood
        artifact = passage.context.artifact
        node_sets["moods"].add(mood)
        node_sets["artifacts"].add(artifact)

        for tag in passage.context.tags:
            node_sets["tags"].add(tag)
            edge_weights[(f"mood:{mood}", f"tag:{tag}")] += 1
            edge_weights[(f"artifact:{artifact}", f"tag:{tag}")] += 1

        for motif in passage.motifs:
            node_sets["motifs"].add(motif)
            edge_weights[(f"mood:{mood}", f"motif:{motif}")] += 1
            edge_weights[(f"artifact:{artifact}", f"motif:{motif}")] += 1

        edge_weights[(f"mood:{mood}", f"artifact:{artifact}")] += 1

    edges = [
        {"source": source, "target": target, "weight": weight}
        for (source, target), weight in edge_weights.items()
    ]
    edges.sort(key=lambda entry: (entry["source"], entry["target"]))

    fingerprint_basis = "|".join(
        f"{edge['source']}->{edge['target']}:{edge['weight']}" for edge in edges
    )
    fingerprint = hashlib.sha256(fingerprint_basis.encode("utf-8")).hexdigest()[:24]

    return {
        "nodes": {key: sorted(values) for key, values in node_sets.items()},
        "edges": edges,
        "fingerprint": fingerprint,
        "edge_count": len(edges),
    }


def format_resonance_digest(resonance: dict | None) -> str:
    """Render a compact summary of the tri-band resonance graph."""

    if not resonance:
        return "No resonance graph available."

    lines = [
        "Tri-Band Creative Resonance", "------------------------------", f"Fingerprint: {resonance.get('fingerprint', 'n/a')}"
    ]

    for band in ("moods", "artifacts", "tags", "motifs"):
        values = resonance.get("nodes", {}).get(band, [])
        lines.append(f"{band.title()}: {', '.join(values) if values else 'none'}")

    edges = resonance.get("edges", [])
    strongest = sorted(edges, key=lambda entry: entry.get("weight", 0), reverse=True)[:5]
    if strongest:
        lines.append("\nStrongest Paths:")
        for edge in strongest:
            lines.append(
                f"- {edge['source']} → {edge['target']} (x{edge['weight']})"
            )
    else:
        lines.append("\nStrongest Paths: none captured")

    return "\n".join(lines)


def analyze_passages(passages: Sequence[FluxPassage], *, library: FluxLibrary | None = None) -> dict:
    """Compute lexical analytics for an iterable of passages."""

    per_passage = []
    total_words = 0
    total_characters = 0
    total_unique: set[str] = set()
    diversity_sum = 0.0
    for index, passage in enumerate(passages, start=1):
        metrics = compute_passage_metrics(passage)
        metrics["index"] = index
        per_passage.append(metrics)
        total_words += metrics["word_count"]
        total_characters += metrics["character_count"]
        diversity_sum += metrics["lexical_diversity"]
        prompt_tokens = _tokenize(passage.prompt)
        closing_tokens = _tokenize(passage.closing)
        total_unique.update(prompt_tokens)
        total_unique.update(closing_tokens)

    aggregate = {
        "total_passages": len(passages),
        "total_words": total_words,
        "average_words": (total_words / len(passages)) if passages else 0,
        "total_characters": total_characters,
        "average_characters": (total_characters / len(passages)) if passages else 0,
        "vocabulary_size": len(total_unique),
        "average_lexical_diversity": round(
            (diversity_sum / len(passages)) if passages else 0.0, 3
        ),
        "session_lexical_diversity": round(
            (len(total_unique) / total_words) if total_words else 0.0, 3
        ),
    }

    coverage = compute_library_coverage(passages, library) if library else None

    return {"per_passage": per_passage, "aggregate": aggregate, "coverage": coverage}


def format_metrics_table(analysis: dict) -> str:
    """Render lexical analytics in a table-like layout."""

    if not analysis.get("per_passage"):
        return "No passages generated."

    headers = [
        "#",
        "Mood",
        "Artifact",
        "Words",
        "Unique",
        "LexDiv",
        "Chars",
        "Prompt",
        "Closing",
        "Label",
    ]
    rows = []
    for metrics in analysis["per_passage"]:
        rows.append(
            [
                str(metrics["index"]),
                metrics["mood"],
                metrics["artifact"],
                str(metrics["word_count"]),
                str(metrics["unique_words"]),
                f"{metrics['lexical_diversity']:.3f}",
                str(metrics["character_count"]),
                str(metrics["prompt_words"]),
                str(metrics["closing_words"]),
                metrics.get("label") or "-",
            ]
        )

    widths = [max(len(row[col]) for row in [headers] + rows) for col in range(len(headers))]

    def _format_row(row: list[str]) -> str:
        return " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row))

    table_lines = [_format_row(headers), "-+-".join("-" * width for width in widths)]
    table_lines.extend(_format_row(row) for row in rows)

    aggregate = analysis.get("aggregate", {})
    table_lines.append(
        (
            "\nTotals: {words} words, {characters} characters across {count} passages"
            " | Avg words: {avg_words:.2f} | Avg chars: {avg_characters:.2f}"
            " | Vocabulary: {vocab} | Avg lex div: {avg_lex:.3f} | Session lex div: {session_lex:.3f}"
        ).format(
            words=aggregate.get("total_words", 0),
            characters=aggregate.get("total_characters", 0),
            count=aggregate.get("total_passages", 0),
            avg_words=aggregate.get("average_words", 0),
            avg_characters=aggregate.get("average_characters", 0),
            vocab=aggregate.get("vocabulary_size", 0),
            avg_lex=aggregate.get("average_lexical_diversity", 0),
            session_lex=aggregate.get("session_lexical_diversity", 0),
        )
    )

    return "\n".join(table_lines)


def format_coverage_section(coverage: dict) -> str:
    """Render a human-readable snapshot of library coverage."""

    lines = ["Library Coverage", "----------------"]
    for key in ("moods", "artifacts", "prompts", "closings"):
        if key not in coverage:
            continue
        stats = coverage[key]
        lines.append(
            "{title}: {count}/{total} ({percent:.2f}%)".format(
                title=key.title(), count=stats.get("count", 0), total=stats.get("total", 0), percent=stats.get("percent", 0.0)
            )
        )
    return "\n".join(lines)


def export_passages(
    path: Path,
    passages: Sequence[FluxPassage],
    summary: dict,
    analytics: dict | None,
    *,
    cli_format: str,
    seed: int | None,
    export_format: str,
    resonance: dict | None,
) -> None:
    """Persist generated passages to *path* in the requested format."""

    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.utcnow().isoformat()
    metadata = {
        "generated_at": generated_at,
        "seed": seed,
        "cli_format": cli_format,
        "count": len(passages),
        "summary": summary,
        "analytics": analytics,
        "resonance": resonance,
    }

    if export_format == "json":
        payload = {**metadata, "passages": [p.to_dict() for p in passages]}
        path.write_text(json.dumps(payload, indent=2))
        return

    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "metadata", **metadata}) + "\n")
        for index, passage in enumerate(passages, start=1):
            handle.write(
                json.dumps(
                    {
                        "type": "passage",
                        "index": index,
                        "payload": passage.to_dict(),
                    }
                )
                + "\n"
            )


def write_markdown_report(
    path: Path,
    *,
    passages: Sequence[FluxPassage],
    summary: dict,
    analytics: dict | None,
    top_words: Sequence[tuple[str, int]],
    seed: int | None,
    mood_cycle: Sequence[str] | None,
    tags: Sequence[str] | None,
    motifs: Sequence[str] | None,
    resonance: dict | None,
) -> None:
    """Create a Markdown report capturing the generated session."""

    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.utcnow().isoformat()

    lines = [
        "# Echo Creative Flux Report",
        "",
        f"- Generated at: {generated_at}",
        f"- Passages: {len(passages)}",
        f"- Seed: {seed if seed is not None else 'random'}",
    ]
    if mood_cycle:
        lines.append(f"- Mood cycle: {', '.join(mood_cycle)}")
    if tags:
        lines.append(f"- CLI tags: {', '.join(tags)}")
    if motifs:
        lines.append(f"- Motifs: {', '.join(motifs)}")

    lines.append("\n## Summary\n")
    lines.append(format_summary(summary))

    if top_words:
        lines.append("\n## Top Words\n")
        for word, count in top_words:
            lines.append(f"- {word}: {count}")
    else:
        lines.append("\n## Top Words\nNo qualifying words captured.")

    if analytics:
        table = format_metrics_table(analytics)
        lines.append("\n## Lexical Metrics\n")
        lines.append("```\n" + table + "\n```")
        coverage = analytics.get("coverage") if isinstance(analytics, dict) else None
        if coverage:
            lines.append("\n## Library Coverage\n")
            lines.append(format_coverage_section(coverage))

    if resonance:
        lines.append("\n## Tri-Band Resonance Fingerprint\n")
        lines.append("```\n" + format_resonance_digest(resonance) + "\n```")

    lines.append("\n## Passages\n")
    for index, passage in enumerate(passages, start=1):
        lines.append(f"### Passage {index}")
        lines.append(passage.render())
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def format_library_listing(library: FluxLibrary) -> str:
    """Return a human-readable representation of the available entries."""

    lines = []
    for title, values in (
        ("Prompts", library.prompts),
        ("Closings", library.closings),
        ("Artifacts", library.artifacts),
        ("Moods", library.moods),
    ):
        entries = list(values)
        lines.append(f"{title} ({len(entries)} entries):")
        for value in entries:
            lines.append(f"  - {value}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _positive_int(value: str) -> int:
    as_int = int(value)
    if as_int < 1:
        raise argparse.ArgumentTypeError("count must be at least 1")
    return as_int


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Echo Creative Flux passages.")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for deterministic output.")
    parser.add_argument(
        "--count",
        type=_positive_int,
        default=1,
        help="Number of passages to generate (ignored when --session-plan is used).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "journal"],
        default="text",
        help="Render passages as plain text, JSON, Markdown, or journal output.",
    )
    parser.add_argument("--mood", type=str, default=None, help="Force a specific mood from the library.")
    parser.add_argument(
        "--artifact",
        type=str,
        default=None,
        help="Force a specific artifact from the library.",
    )
    parser.add_argument(
        "--label",
        type=str,
        default=None,
        help="Optional label appended to every generated header (unless overridden by a session plan).",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=None,
        help="Attach one or more tags to every passage (repeat flag for multiple tags).",
    )
    parser.add_argument(
        "--motif",
        action="append",
        dest="motifs",
        default=None,
        help="Weave repeating motif phrases into prompts and closings (repeat flag for multiple motifs).",
    )
    parser.add_argument(
        "--motif-style",
        choices=["suffix", "prefix", "inline"],
        default="suffix",
        help="Control how motifs are blended: appended, prepended, or inline brackets.",
    )
    parser.add_argument(
        "--library",
        type=Path,
        default=None,
        help="Optional JSON file describing prompts, closings, artifacts, and moods.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Spacing in minutes between timestamps when generating multiple passages.",
    )
    parser.add_argument(
        "--mood-cycle",
        type=str,
        default=None,
        help="Comma-separated moods to cycle through when no explicit mood is provided.",
    )
    parser.add_argument(
        "--artifact-cycle",
        type=str,
        default=None,
        help="Comma-separated artifacts to cycle through when --artifact is not supplied.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a counts summary for moods and artifacts after generation.",
    )
    parser.add_argument(
        "--analytics",
        choices=["none", "table", "json"],
        default="none",
        help="Optionally display lexical analytics for generated passages.",
    )
    parser.add_argument(
        "--list-library",
        action="store_true",
        help="Display the available library entries and exit.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help="Write generated passages to this file (JSON or JSONL).",
    )
    parser.add_argument(
        "--export-format",
        choices=["json", "jsonl"],
        default="json",
        help="File format used when --export is provided.",
    )
    parser.add_argument(
        "--session-plan",
        type=Path,
        default=None,
        help="JSON file describing a structured session; overrides --count and timestamp spacing.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write a Markdown report that captures the session summary and analytics.",
    )
    parser.add_argument(
        "--report-top-n",
        type=int,
        default=10,
        help="Number of top lexical tokens to include inside --report output.",
    )
    parser.add_argument(
        "--stopwords-file",
        action="append",
        type=Path,
        default=None,
        help=(
            "Path to a file containing extra stopwords (one per line); "
            "may be repeated to combine multiple lists."
        ),
    )
    parser.add_argument(
        "--top-words",
        type=int,
        default=0,
        help="If greater than zero, list the most common lexical tokens after generation.",
    )
    parser.add_argument(
        "--resonance-graph",
        type=Path,
        default=None,
        help=(
            "Write the world's first tri-band creative resonance map (mood/artifact/motif) "
            "as JSON to this path."
        ),
    )
    parser.add_argument(
        "--resonance-digest",
        action="store_true",
        help="Print the tri-band resonance fingerprint and strongest paths after generation.",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    library = DEFAULT_LIBRARY
    if args.library is not None:
        library = FluxLibrary.from_json_file(args.library, fallback=DEFAULT_LIBRARY)

    if args.report_top_n <= 0:
        parser.error("--report-top-n must be a positive integer.")
    if args.top_words < 0:
        parser.error("--top-words must be zero or a positive integer.")

    extra_stopwords = _load_stopwords(args.stopwords_file)

    session_plan = SessionPlan.from_json_file(args.session_plan) if args.session_plan else None

    mood_cycle: list[str] | None = None
    if args.mood_cycle:
        mood_cycle = [value.strip() for value in args.mood_cycle.split(",") if value.strip()]
        if not mood_cycle:
            parser.error("--mood-cycle must include at least one valid mood name.")
        invalid = [value for value in mood_cycle if value not in library.moods]
        if invalid:
            parser.error(
                "--mood-cycle entries must be valid moods from the library. Invalid: "
                + ", ".join(invalid)
            )

    artifact_cycle: list[str] | None = None
    if args.artifact_cycle:
        artifact_cycle = [value.strip() for value in args.artifact_cycle.split(",") if value.strip()]
        if not artifact_cycle:
            parser.error("--artifact-cycle must include at least one valid artifact name.")
        invalid_artifacts = [value for value in artifact_cycle if value not in library.artifacts]
        if invalid_artifacts:
            parser.error(
                "--artifact-cycle entries must be valid artifacts from the library. Invalid: "
                + ", ".join(invalid_artifacts)
            )

    cli_tags = [tag.strip() for tag in (args.tags or []) if tag and tag.strip()]
    motifs = [motif.strip() for motif in (args.motifs or []) if motif and motif.strip()]

    base_timestamp = datetime.utcnow()
    interval_delta = timedelta(minutes=args.interval) if args.interval else None
    if args.list_library:
        print(format_library_listing(library))
        return

    def resolve_mood(index: int, explicit: str | None) -> str | None:
        if explicit:
            return explicit
        if args.mood:
            return args.mood
        if mood_cycle:
            return mood_cycle[index % len(mood_cycle)]
        return None

    def resolve_artifact(index: int, explicit: str | None) -> str | None:
        if explicit:
            return explicit
        if args.artifact:
            return args.artifact
        if artifact_cycle:
            return artifact_cycle[index % len(artifact_cycle)]
        return None

    def collect_tags(entry_tags: list[str] | None) -> list[str] | None:
        combined: list[str] = []
        if cli_tags:
            combined.extend(cli_tags)
        if entry_tags:
            combined.extend(entry_tags)
        return combined or None

    passages: list[FluxPassage] = []
    if session_plan is not None:
        plan_base = session_plan.base_timestamp or base_timestamp
        for index, entry in enumerate(session_plan.entries):
            timestamp: datetime | None = None
            if entry.offset_minutes is not None:
                timestamp = plan_base + timedelta(minutes=float(entry.offset_minutes))
            elif session_plan.base_timestamp is not None:
                timestamp = plan_base
            elif interval_delta is not None:
                timestamp = plan_base + interval_delta * index

            passages.append(
                generate_passage(
                    rng,
                    library=library,
                    mood=resolve_mood(index, entry.mood),
                    artifact=resolve_artifact(index, entry.artifact),
                    timestamp=timestamp,
                    label=entry.label or args.label,
                    tags=collect_tags(entry.tags),
                    motifs=motifs,
                    motif_style=args.motif_style,
                )
            )
    else:
        for index in range(args.count):
            timestamp = (base_timestamp + interval_delta * index) if interval_delta else None
            passages.append(
                generate_passage(
                    rng,
                    library=library,
                    mood=resolve_mood(index, None),
                    artifact=resolve_artifact(index, None),
                    timestamp=timestamp,
                    label=args.label,
                    tags=collect_tags(None),
                    motifs=motifs,
                    motif_style=args.motif_style,
                )
            )

    summary = summarize_passages(passages)
    analytics: dict | None = None
    needs_analytics = args.analytics != "none" or args.export is not None or args.report is not None
    if needs_analytics:
        analytics = analyze_passages(passages, library=library)

    resonance: dict | None = None
    needs_resonance = (
        args.resonance_graph is not None
        or args.resonance_digest
        or args.report is not None
        or args.export is not None
    )
    if needs_resonance:
        resonance = build_resonance_graph(passages)

    if args.format == "json":
        payload = [passage.to_dict() for passage in passages]
        print(json.dumps(payload, indent=2))
    elif args.format == "markdown":
        for passage in passages:
            header = passage.context.render_header()
            body = f"> {passage.prompt}\n\n_{passage.closing}_"
            print(f"## {header}\n\n{body}\n")
    elif args.format == "journal":
        for index, passage in enumerate(passages, start=1):
            header = passage.context.render_header()
            print(f"### Entry {index}")
            print(header)
            print(f"Mood: {passage.context.mood} | Artifact: {passage.context.artifact}")
            print(f"Prompt: {passage.prompt}")
            print(f"Closing: {passage.closing}\n")
        print("Summary:")
        print(json.dumps(summary, indent=2))
    else:
        for index, passage in enumerate(passages):
            if index:
                print("\n---\n")
            print(passage.render())

    if args.analytics == "table" and analytics is not None:
        print("\n" + format_metrics_table(analytics))
        if analytics.get("coverage"):
            print("\n" + format_coverage_section(analytics["coverage"]))
    elif args.analytics == "json" and analytics is not None:
        print("\n" + json.dumps(analytics, indent=2))

    if args.resonance_digest and resonance is not None:
        print("\n" + format_resonance_digest(resonance))

    if args.export is not None:
        export_passages(
            args.export,
            passages,
            summary,
            analytics,
            cli_format=args.format,
            seed=args.seed,
            export_format=args.export_format,
            resonance=resonance,
        )

    if args.report is not None:
        top_words = compute_top_words(passages, limit=args.report_top_n, stopwords=extra_stopwords)
        write_markdown_report(
            args.report,
            passages=passages,
            summary=summary,
            analytics=analytics,
            top_words=top_words,
            seed=args.seed,
            mood_cycle=mood_cycle or [],
            tags=cli_tags,
            motifs=motifs,
            resonance=resonance,
        )

    if args.summary:
        print("\n" + format_summary(summary))

    if args.top_words:
        words = compute_top_words(passages, limit=args.top_words, stopwords=extra_stopwords)
        if words:
            print("\nTop Words:")
            for token, count in words:
                print(f"- {token}: {count}")
        else:
            print("\nTop Words: No lexical tokens available.")

    if args.resonance_graph is not None and resonance is not None:
        args.resonance_graph.parent.mkdir(parents=True, exist_ok=True)
        args.resonance_graph.write_text(json.dumps(resonance, indent=2), encoding="utf-8")
        print(
            "\nTri-band resonance map written to "
            f"{args.resonance_graph} (edge count: {resonance.get('edge_count', 0)})"
        )


if __name__ == "__main__":
    main()
