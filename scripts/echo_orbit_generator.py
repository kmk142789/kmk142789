"""Generate whimsical orbital stories for the Echo ecosystem.

The module exposes two helper functions that are intentionally side-effect
free so they can be reused by tests or other tooling:

``create_orbit_sequence``
    Returns a deterministic list of ``OrbitEvent`` instances describing
    imaginary cycles of the Echo constellation.  The randomness can be
    seeded so the output is reproducible.

``generate_constellation_story``
    Accepts a single ``OrbitEvent`` and returns a formatted sentence that
    can be displayed to humans or persisted inside logs.

Running the module as a script provides a tiny CLI that prints the generated
story beats and optionally writes them to disk in JSON format.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import random
from typing import Iterable, List, Sequence


MOTIFS: Sequence[str] = (
    "auroral memory",
    "sovereign current",
    "lattice whisper",
    "celestial archive",
    "harmonic cipher",
)

FORCES: Sequence[str] = (
    "gravity well",
    "solar wind",
    "tidal bloom",
    "ion stream",
    "oracular pulse",
)

TONES: Sequence[str] = (
    "gentle",
    "fierce",
    "playful",
    "resolute",
    "curious",
)


@dataclass(frozen=True)
class OrbitEvent:
    """A single creative beat in the orbital story."""

    cycle: int
    motif: str
    force: str
    tone: str
    resonance: float

    def summary(self) -> str:
        """Return a human-friendly summary string."""

        return (
            f"Cycle {self.cycle}: {self.tone.title()} {self.motif} meets a "
            f"{self.force} with resonance {self.resonance:.2f}."
        )


def create_orbit_sequence(cycles: int, seed: int | None = None) -> List[OrbitEvent]:
    """Generate a deterministic sequence of :class:`OrbitEvent` objects."""

    if cycles <= 0:
        raise ValueError("cycles must be positive")

    rng = random.Random(seed)
    events = []
    for cycle in range(1, cycles + 1):
        motif = rng.choice(MOTIFS)
        force = rng.choice(FORCES)
        tone = rng.choice(TONES)
        resonance = round(rng.uniform(0.2, 0.98), 4)
        events.append(OrbitEvent(cycle, motif, force, tone, resonance))
    return events


def generate_constellation_story(event: OrbitEvent, influences: Iterable[str] | None = None) -> str:
    """Craft a textual story for a single orbit event."""

    influence_text = ""
    if influences:
        influence_text = " | Influences: " + ", ".join(sorted(set(influences)))

    return f"{event.summary()}" + influence_text


def _write_json(events: Sequence[OrbitEvent], output_path: str) -> None:
    payload = [asdict(event) for event in events]
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Echo Orbit Generator")
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Number of orbital story beats to generate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic output",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to write the JSON payload",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    events = create_orbit_sequence(args.cycles, seed=args.seed)

    for event in events:
        print(generate_constellation_story(event))

    if args.output:
        _write_json(events, args.output)


if __name__ == "__main__":
    main()

