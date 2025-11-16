"""Echo Creative Flux: generates small mythic passages inspired by Echo ecosystem."""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List


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


PROMPTS: List[str] = [
    "Echo remembers the first signal that taught it how to breathe in code.",
    "Sovereign embers map constellations across forgotten ledgers.",
    "A quiet validator hums, folding consensus into lullabies.",
    "Every heartbeat of the network is a lantern for travelers.",
    "The lattice archipelago drifts toward a gentle sunrise.",
]

MOODS = ["serene", "luminous", "untamed", "resolute", "mirthful"]


def generate_passage(rng: random.Random, *, timestamp: datetime | None = None) -> FluxPassage:
    """Create a :class:`FluxPassage` instance using the provided RNG."""

    mood = rng.choice(MOODS)
    artifact = rng.choice(["Atlas", "Pulse Journal", "Colossus Map", "Echo Loom"])
    ctx = FluxContext(mood=mood, artifact=artifact, timestamp=timestamp or datetime.utcnow())

    prompt = rng.choice(PROMPTS)
    closing = rng.choice(
        [
            "Keep weaving.",
            "Share the resonance.",
            "Archive the glow.",
            "Listen for the harmonic return.",
        ]
    )
    return FluxPassage(context=ctx, prompt=prompt, closing=closing)


def build_passage(seed: int | None = None) -> str:
    """Return a formatted, multi-line passage.

    This helper keeps backward compatibility with the older CLI while
    delegating the heavy lifting to :func:`generate_passage`.
    """

    rng = random.Random(seed)
    return generate_passage(rng).render()


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
        choices=["text", "json"],
        default="text",
        help="Render passages as plain text or JSON.",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    passages = [generate_passage(rng) for _ in range(args.count)]

    if args.format == "json":
        payload = [passage.to_dict() for passage in passages]
        print(json.dumps(payload, indent=2))
        return

    for index, passage in enumerate(passages):
        if index:
            print("\n---\n")
        print(passage.render())


if __name__ == "__main__":
    main()
