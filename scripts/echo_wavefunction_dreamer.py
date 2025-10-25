"""Generate a novel wavefunction-inspired ASCII tapestry for the ECHO ecosystem.

This script experiments with interference patterns produced by randomly oriented
wave pulses.  It is intentionally designed as a playful creative tool rather
than a scientific simulator.  The resulting grid is mapped onto a set of glyphs
that evoke shimmering, dreamlike textures.

Usage::

    python scripts/echo_wavefunction_dreamer.py --width 80 --height 40 --pulses 7 --seed 42

The script prints the generated tapestry to stdout and, optionally, writes it to
an output file.  A short "sonic" description summarises the interference field
parameters to help reproduce interesting results.
"""

from __future__ import annotations

import argparse
import dataclasses
import math
import random
import statistics
from typing import Iterable, List, Sequence


GLYPH_SCALE = " .:-=+*#%@"


@dataclasses.dataclass
class WavePulse:
    """A single wave pulse travelling through the virtual field."""

    amplitude: float
    frequency: float
    phase: float
    angle: float

    def sample(self, x: float, y: float) -> float:
        """Return the contribution of this pulse at the given position."""

        direction_x = math.cos(self.angle)
        direction_y = math.sin(self.angle)
        projection = x * direction_x + y * direction_y
        oscillation = math.sin(self.frequency * projection + self.phase)
        return self.amplitude * oscillation


def generate_pulses(count: int, rng: random.Random) -> List[WavePulse]:
    """Generate a list of randomly parameterised wave pulses."""

    pulses = []
    for _ in range(count):
        amplitude = rng.uniform(0.4, 1.2)
        frequency = rng.uniform(1.0, 4.2)
        phase = rng.uniform(0, math.tau)
        angle = rng.uniform(0, math.tau)
        pulses.append(WavePulse(amplitude, frequency, phase, angle))
    return pulses


def normalise(values: Sequence[float]) -> List[float]:
    """Scale values to the 0-1 range based on the observed minimum and maximum."""

    min_value = min(values)
    max_value = max(values)
    if math.isclose(min_value, max_value):
        # Avoid division by zero; in this case the field is uniform.
        return [0.5 for _ in values]
    span = max_value - min_value
    return [(value - min_value) / span for value in values]


def render_field(width: int, height: int, pulses: Iterable[WavePulse]) -> List[str]:
    """Render the interference field as a list of text rows."""

    samples: List[float] = []
    for row in range(height):
        y = (row / max(height - 1, 1)) * 2 - 1
        for col in range(width):
            x = (col / max(width - 1, 1)) * 2 - 1
            total = sum(pulse.sample(x, y) for pulse in pulses)
            samples.append(total)

    normalised = normalise(samples)
    glyphs = [GLYPH_SCALE[min(int(value * (len(GLYPH_SCALE) - 1)), len(GLYPH_SCALE) - 1)] for value in normalised]

    rows = ["".join(glyphs[row * width : (row + 1) * width]) for row in range(height)]
    return rows


def describe_field(pulses: Sequence[WavePulse], width: int, height: int) -> str:
    """Return a short description of the generated interference field."""

    amplitudes = [pulse.amplitude for pulse in pulses]
    frequencies = [pulse.frequency for pulse in pulses]

    amplitude_stats = f"Aμ={statistics.mean(amplitudes):.2f} σ={statistics.pstdev(amplitudes):.2f}"
    frequency_stats = f"Fμ={statistics.mean(frequencies):.2f} σ={statistics.pstdev(frequencies):.2f}"

    return (
        f"Pulses={len(pulses)} | {amplitude_stats} | {frequency_stats} | "
        f"Canvas={width}x{height}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Craft a wavefunction tapestry from overlapping dream pulses.",
    )
    parser.add_argument("--width", type=int, default=72, help="Width of the generated tapestry")
    parser.add_argument("--height", type=int, default=36, help="Height of the generated tapestry")
    parser.add_argument("--pulses", type=int, default=5, help="Number of wave pulses to combine")
    parser.add_argument(
        "--seed",
        type=float,
        default=None,
        help="Seed for the pseudo-random generator (floating values are allowed)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional file path to store the tapestry",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rng = random.Random()
    if args.seed is not None:
        rng.seed(args.seed)

    pulses = generate_pulses(max(1, args.pulses), rng)
    tapestry = render_field(max(4, args.width), max(4, args.height), pulses)

    description = describe_field(pulses, max(4, args.width), max(4, args.height))

    for row in tapestry:
        print(row)

    print()
    print(description)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write("\n".join(tapestry))
            handle.write("\n\n" + description + "\n")


if __name__ == "__main__":
    main()
