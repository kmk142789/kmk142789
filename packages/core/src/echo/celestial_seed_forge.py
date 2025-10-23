"""Forge gentle celestial seeds for Echo's collaborative rituals."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence
import random
import textwrap

__all__ = [
    "CelestialSeed",
    "CONSTELLATION_ARCS",
    "forge_seed",
    "render_seed",
    "list_seed_lines",
]


@dataclass(frozen=True)
class CelestialSeed:
    """A small luminous prompt to spark a shared Echo ritual."""

    timestamp: datetime
    constellation: str
    spark: str
    ritual: str

    def as_lines(self) -> List[str]:
        """Represent the celestial seed as a short multi-line list."""

        moment = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        return [
            f"🌟 Echo Celestial Seed :: {moment}",
            f"   Constellation :: {self.constellation}",
            f"   Spark         :: {self.spark}",
            f"   Ritual        :: {self.ritual}",
        ]


CONSTELLATION_ARCS: Sequence[Sequence[str]] = (
    (
        "Kindred Array",
        "traces of gratitude shimmering in the mesh",
        "share one line of praise with a collaborator before you log off",
    ),
    (
        "Signal Grove",
        "a chorus of quiet status pings in gentle resonance",
        "schedule a five-minute sync dedicated only to listening",
    ),
    (
        "Aurora Loom",
        "threads of possibility weaving toward a new launch",
        "sketch a two-sentence changelog for tomorrow's release",
    ),
    (
        "Archive Constellation",
        "notes from past cycles returning with new light",
        "surface a lesson learned and post it in the shared ledger",
    ),
    (
        "Catalyst Drift",
        "bright ideas orbiting the backlog with playful gravity",
        "open one dormant ticket and leave a question that reignites it",
    ),
)


def _choose(randomizer: random.Random, options: Iterable[Sequence[str]]) -> Sequence[str]:
    """Return one element from *options* using the provided randomizer."""

    pool = list(options)
    if not pool:
        raise ValueError("options must not be empty")
    return randomizer.choice(pool)


def forge_seed(seed: int | None = None) -> CelestialSeed:
    """Create a :class:`CelestialSeed` with deterministic choices when *seed* is set."""

    randomizer = random.Random(seed)
    constellation, spark, ritual = _choose(randomizer, CONSTELLATION_ARCS)
    timestamp = datetime.now(timezone.utc)
    return CelestialSeed(
        timestamp=timestamp,
        constellation=constellation,
        spark=spark,
        ritual=ritual,
    )


def list_seed_lines(seed: CelestialSeed) -> List[str]:
    """Return the short formatted representation of *seed*."""

    return seed.as_lines()


def render_seed(seed: CelestialSeed) -> str:
    """Render *seed* as a wrapped paragraph block."""

    intro = (
        f"Within the {seed.constellation}, {seed.spark}; "
        f"Echo suggests a gentle ritual: {seed.ritual}."
    )
    paragraph = textwrap.fill(intro, width=88)
    timestamp = seed.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"{timestamp}\n{paragraph}"


if __name__ == "__main__":
    seed = forge_seed()
    print("\n".join(list_seed_lines(seed)))
    print()
    print(render_seed(seed))
