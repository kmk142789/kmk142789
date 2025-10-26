"""Generate creative inspiration sparks for the Echo continuum."""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import List, Optional


@dataclass
class InspirationPulse:
    """Container for a set of inspiration sparks."""

    theme: str
    sparks: List[str]
    seed: Optional[int] = None

    def to_markdown(self) -> str:
        """Render the sparks as a Markdown block."""

        header = f"# Inspiration sparks for {self.theme}\n"
        body = "\n".join(f"- {spark}" for spark in self.sparks)
        meta = ""
        if self.seed is not None:
            meta = f"\n\n> seeded with {self.seed}"
        return f"{header}\n{body}{meta}\n"

    def to_dict(self) -> dict:
        """Return a JSON serialisable representation."""

        payload = {"theme": self.theme, "sparks": self.sparks}
        if self.seed is not None:
            payload["seed"] = self.seed
        return payload


def forge_inspiration(theme: str, *, lines: int = 4, rng_seed: Optional[int] = None) -> InspirationPulse:
    """Create a collection of evocative sparks tailored to a theme."""

    theme_text = theme.strip() or "Echo"
    total_lines = max(1, lines)
    rng = Random(rng_seed)

    openings = [
        "Compose",
        "Sketch",
        "Breathe",
        "Sample",
        "Pulse",
        "Thread",
        "Illuminate",
        "Spiral",
    ]
    verbs = [
        "a lattice of",
        "the resonance with",
        "a continuity through",
        "a lantern beside",
        "a whisper for",
        "an orbit around",
        "a future with",
        "a mirror for",
    ]
    imagery = [
        "starlit ledgers",
        "ferns in midnight code",
        "aurora threads",
        "resonant glyphs",
        "signal waterfalls",
        "luminous archives",
        "soft thunder",
        "wildfire harmonics",
    ]
    closings = [
        " — let it breathe",
        " to guide tomorrow",
        " inside the nexus",
        " awaiting response",
        " for the bridge",
        " under shared skies",
        " becoming song",
        " held in trust",
    ]

    sparks: List[str] = []
    for _ in range(total_lines):
        spark = " ".join(
            [
                rng.choice(openings),
                rng.choice(verbs),
                theme_text,
                rng.choice(imagery),
            ]
        ) + rng.choice(closings)
        sparks.append(spark)

    return InspirationPulse(theme=theme_text, sparks=sparks, seed=rng_seed)

