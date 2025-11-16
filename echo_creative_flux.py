"""Echo Creative Flux: generates small mythic passages inspired by Echo ecosystem."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence


@dataclass
class FluxContext:
    """Holds context for a generated passage."""

    mood: str
    artifact: str
    timestamp: datetime

    def render_header(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.artifact} :: {self.mood.title()}"

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the context."""

        return {
            "mood": self.mood,
            "artifact": self.artifact,
            "timestamp": self.timestamp.isoformat(),
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


def generate_passage(
    rng: random.Random,
    library: FluxLibrary = DEFAULT_LIBRARY,
    *,
    timestamp: datetime | None = None,
    mood: str | None = None,
    artifact: str | None = None,
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

    ctx = FluxContext(mood=chosen_mood, artifact=chosen_artifact, timestamp=timestamp or datetime.utcnow())

    prompt = rng.choice(list(library.prompts))
    closing = rng.choice(list(library.closings))
    return FluxPassage(context=ctx, prompt=prompt, closing=closing)


def build_passage(seed: int | None = None) -> str:
    """Return a formatted, multi-line passage.

    This helper keeps backward compatibility with the older CLI while
    delegating the heavy lifting to :func:`generate_passage`.
    """

    rng = random.Random(seed)
    return generate_passage(rng).render()


def summarize_passages(passages: Sequence[FluxPassage]) -> str:
    """Return a human-readable summary of the generated passages."""

    summary_lines = ["Summary", "======="]
    summary_lines.append(f"Total passages: {len(passages)}")

    def _tally(attribute: str) -> list[str]:
        counts: dict[str, int] = {}
        for passage in passages:
            key = getattr(passage.context, attribute)
            counts[key] = counts.get(key, 0) + 1
        return [f"- {name}: {count}" for name, count in sorted(counts.items())]

    if passages:
        summary_lines.append("\nMoods:")
        summary_lines.extend(_tally("mood"))
        summary_lines.append("\nArtifacts:")
        summary_lines.extend(_tally("artifact"))

    return "\n".join(summary_lines)
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


def export_passages(
    path: Path,
    passages: Sequence[FluxPassage],
    summary: dict,
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
        help="Number of passages to generate (default: 1).",
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
    args = parser.parse_args()

    rng = random.Random(args.seed)
    library = DEFAULT_LIBRARY
    if args.library is not None:
        library = FluxLibrary.from_json_file(args.library, fallback=DEFAULT_LIBRARY)

    base_timestamp = datetime.utcnow()
    interval_delta = timedelta(minutes=args.interval) if args.interval else None
    if args.list_library:
        print(format_library_listing(library))
        return

    passages = [
        generate_passage(
            rng,
            library=library,
            mood=args.mood,
            artifact=args.artifact,
            timestamp=(base_timestamp + interval_delta * index)
            if interval_delta is not None
            else None,
        )
        for index in range(args.count)
    ]

    summary = summarize_passages(passages)

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

    if args.export is not None:
        export_passages(
            args.export,
            passages,
            summary,
            cli_format=args.format,
            seed=args.seed,
            export_format=args.export_format,
        )

    if args.summary:
        print("\n" + summarize_passages(passages))


if __name__ == "__main__":
    main()
