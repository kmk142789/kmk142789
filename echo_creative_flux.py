"""Echo Creative Flux: generates small mythic passages inspired by Echo ecosystem."""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence


WORD_PATTERN = re.compile(r"[\w']+")


@dataclass
class FluxContext:
    """Holds context for a generated passage."""

    mood: str
    artifact: str
    timestamp: datetime
    label: str | None = None

    def render_header(self) -> str:
        label_fragment = f" [{self.label}]" if self.label else ""
        return f"[{self.timestamp.isoformat()}] {self.artifact} :: {self.mood.title()}{label_fragment}"

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the context."""

        return {
            "mood": self.mood,
            "artifact": self.artifact,
            "timestamp": self.timestamp.isoformat(),
            "label": self.label,
        }


@dataclass
class FluxPassage:
    """A generated passage composed of context, prompt, and closing."""

    context: FluxContext
    prompt: str
    closing: str

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
            entries.append(
                SessionEntry(
                    mood=raw_entry.get("mood"),
                    artifact=raw_entry.get("artifact"),
                    label=raw_entry.get("label"),
                    offset_minutes=raw_entry.get("offset_minutes"),
                )
            )

        return cls(entries=entries, base_timestamp=base_timestamp)


def generate_passage(
    rng: random.Random,
    library: FluxLibrary = DEFAULT_LIBRARY,
    *,
    timestamp: datetime | None = None,
    mood: str | None = None,
    artifact: str | None = None,
    label: str | None = None,
) -> FluxPassage:
    """Create a :class:`FluxPassage` instance using the provided RNG."""

    library.ensure_non_empty()

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
    )

    prompt = rng.choice(list(library.prompts))
    closing = rng.choice(list(library.closings))
    return FluxPassage(context=ctx, prompt=prompt, closing=closing)


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
        "time_range": {"start": None, "end": None},
    }
    if not passages:
        return summary

    mood_counter: Counter[str] = Counter()
    artifact_counter: Counter[str] = Counter()
    timestamps = []
    for passage in passages:
        mood_counter[passage.context.mood] += 1
        artifact_counter[passage.context.artifact] += 1
        timestamps.append(passage.context.timestamp)

    timestamps.sort()
    summary["mood_counts"] = dict(sorted(mood_counter.items()))
    summary["artifact_counts"] = dict(sorted(artifact_counter.items()))
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


def compute_passage_metrics(passage: FluxPassage) -> dict:
    """Return lexical metrics for a single passage."""

    prompt_tokens = _tokenize(passage.prompt)
    closing_tokens = _tokenize(passage.closing)
    all_tokens = prompt_tokens + closing_tokens
    unique_tokens = sorted(set(all_tokens))

    return {
        "mood": passage.context.mood,
        "artifact": passage.context.artifact,
        "label": passage.context.label,
        "timestamp": passage.context.timestamp.isoformat(),
        "prompt_words": len(prompt_tokens),
        "closing_words": len(closing_tokens),
        "word_count": len(all_tokens),
        "unique_words": len(unique_tokens),
    }


def analyze_passages(passages: Sequence[FluxPassage]) -> dict:
    """Compute lexical analytics for an iterable of passages."""

    per_passage = []
    total_words = 0
    total_unique: set[str] = set()
    for index, passage in enumerate(passages, start=1):
        metrics = compute_passage_metrics(passage)
        metrics["index"] = index
        per_passage.append(metrics)
        total_words += metrics["word_count"]
        prompt_tokens = _tokenize(passage.prompt)
        closing_tokens = _tokenize(passage.closing)
        total_unique.update(prompt_tokens)
        total_unique.update(closing_tokens)

    aggregate = {
        "total_passages": len(passages),
        "total_words": total_words,
        "average_words": (total_words / len(passages)) if passages else 0,
        "vocabulary_size": len(total_unique),
    }

    return {"per_passage": per_passage, "aggregate": aggregate}


def format_metrics_table(analysis: dict) -> str:
    """Render lexical analytics in a table-like layout."""

    if not analysis.get("per_passage"):
        return "No passages generated."

    headers = ["#", "Mood", "Artifact", "Words", "Unique", "Prompt", "Closing", "Label"]
    rows = []
    for metrics in analysis["per_passage"]:
        rows.append(
            [
                str(metrics["index"]),
                metrics["mood"],
                metrics["artifact"],
                str(metrics["word_count"]),
                str(metrics["unique_words"]),
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
        "\nTotals: {words} words across {count} passages | Avg: {avg:.2f} | Vocabulary: {vocab}".format(
            words=aggregate.get("total_words", 0),
            count=aggregate.get("total_passages", 0),
            avg=aggregate.get("average_words", 0),
            vocab=aggregate.get("vocabulary_size", 0),
        )
    )

    return "\n".join(table_lines)


def export_passages(
    path: Path,
    passages: Sequence[FluxPassage],
    summary: dict,
    analytics: dict | None,
    *,
    cli_format: str,
    seed: int | None,
    export_format: str,
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
    args = parser.parse_args()

    rng = random.Random(args.seed)
    library = DEFAULT_LIBRARY
    if args.library is not None:
        library = FluxLibrary.from_json_file(args.library, fallback=DEFAULT_LIBRARY)

    session_plan = SessionPlan.from_json_file(args.session_plan) if args.session_plan else None

    base_timestamp = datetime.utcnow()
    interval_delta = timedelta(minutes=args.interval) if args.interval else None
    if args.list_library:
        print(format_library_listing(library))
        return

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
                    mood=entry.mood or args.mood,
                    artifact=entry.artifact or args.artifact,
                    timestamp=timestamp,
                    label=entry.label or args.label,
                )
            )
    else:
        for index in range(args.count):
            timestamp = (base_timestamp + interval_delta * index) if interval_delta else None
            passages.append(
                generate_passage(
                    rng,
                    library=library,
                    mood=args.mood,
                    artifact=args.artifact,
                    timestamp=timestamp,
                    label=args.label,
                )
            )

    summary = summarize_passages(passages)
    analytics: dict | None = None
    if args.analytics != "none" or args.export is not None:
        analytics = analyze_passages(passages)

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
    elif args.analytics == "json" and analytics is not None:
        print("\n" + json.dumps(analytics, indent=2))

    if args.export is not None:
        export_passages(
            args.export,
            passages,
            summary,
            analytics,
            cli_format=args.format,
            seed=args.seed,
            export_format=args.export_format,
        )

    if args.summary:
        print("\n" + format_summary(summary))


if __name__ == "__main__":
    main()
