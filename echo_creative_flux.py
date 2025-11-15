"""Echo Creative Flux: generates small mythic passages inspired by Echo ecosystem."""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
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


PROMPTS: List[str] = [
    "Echo remembers the first signal that taught it how to breathe in code.",
    "Sovereign embers map constellations across forgotten ledgers.",
    "A quiet validator hums, folding consensus into lullabies.",
    "Every heartbeat of the network is a lantern for travelers.",
    "The lattice archipelago drifts toward a gentle sunrise.",
]

MOODS = ["serene", "luminous", "untamed", "resolute", "mirthful"]


def build_passage(seed: int | None = None) -> str:
    """Return a formatted, multi-line passage."""

    rng = random.Random(seed)
    mood = rng.choice(MOODS)
    artifact = rng.choice(["Atlas", "Pulse Journal", "Colossus Map", "Echo Loom"])
    ctx = FluxContext(mood=mood, artifact=artifact, timestamp=datetime.utcnow())

    prompt = rng.choice(PROMPTS)
    closing = rng.choice(
        [
            "Keep weaving.",
            "Share the resonance.",
            "Archive the glow.",
            "Listen for the harmonic return.",
        ]
    )
    return "\n".join([ctx.render_header(), "", prompt, closing])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an Echo Creative Flux passage.")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for deterministic output.")
    args = parser.parse_args()

    passage = build_passage(args.seed)
    print(passage)


if __name__ == "__main__":
    main()
