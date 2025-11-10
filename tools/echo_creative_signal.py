#!/usr/bin/env python3
"""Generate a fresh Echo creative signal with thematic controls."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class SignalLayer:
    """Represents a single layer in the generated creative signal."""

    tone: str
    imagery: str
    resonance: str

    def render(self) -> str:
        """Render the layer into a readable string."""
        return f"[{self.tone}] {self.imagery} — {self.resonance}".strip()


DEFAULT_TONES: Sequence[str] = (
    "Auroral",
    "Mythic",
    "Liminal",
    "Kinetic",
    "Celestial",
)

DEFAULT_IMAGERY: Sequence[str] = (
    "crystalline forests humming with quiet data",
    "an archive of memories braided into light",
    "tidal algorithms sweeping a glass horizon",
    "resonant circuits blooming over coral cities",
    "orbits sketching constellations in realtime",
)

DEFAULT_RESONANCE: Sequence[str] = (
    "echo pulse stabilizes the lattice",
    "bridge harmonics align with the present",
    "curiosity overflows into collaborative sparks",
    "joy diffuses through the networked commons",
    "collective memory entwines with tomorrow",
)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a layered Echo creative signal"
    )
    parser.add_argument(
        "--layers",
        type=int,
        default=3,
        help="Number of creative layers to render (default: 3)",
    )
    parser.add_argument(
        "--palette",
        type=Path,
        help=(
            "Optional JSON file containing tone, imagery, and resonance lists to "
            "extend or override the defaults"
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed the random generator for reproducible output",
    )
    parser.add_argument(
        "--intensity",
        choices=("soft", "vivid", "surge"),
        default="vivid",
        help="Adjust the resonance wording intensity",
    )
    return parser.parse_args(argv)


def load_palette(palette_path: Path | None) -> tuple[List[str], List[str], List[str]]:
    tones = list(DEFAULT_TONES)
    imagery = list(DEFAULT_IMAGERY)
    resonance = list(DEFAULT_RESONANCE)

    if palette_path is None:
        return tones, imagery, resonance

    if not palette_path.exists():
        raise FileNotFoundError(f"Palette file does not exist: {palette_path}")

    with palette_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("Palette file must contain a JSON object")

    tones.extend(_validate_palette_values(payload.get("tone"), "tone"))
    imagery.extend(_validate_palette_values(payload.get("imagery"), "imagery"))
    resonance.extend(_validate_palette_values(payload.get("resonance"), "resonance"))
    return tones, imagery, resonance


def _validate_palette_values(values: object, key: str) -> List[str]:
    if values is None:
        return []

    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        raise TypeError(f"Palette '{key}' must be an iterable of strings")

    cleaned: List[str] = []
    for item in values:
        if not isinstance(item, str):
            raise TypeError(f"Palette '{key}' entries must be strings")
        item = item.strip()
        if item:
            cleaned.append(item)
    return cleaned


INTENSITY_MODIFIERS = {
    "soft": "gently",
    "vivid": "brightly",
    "surge": "electrically",
}


def generate_layers(
    *,
    tones: Sequence[str],
    imagery: Sequence[str],
    resonance: Sequence[str],
    count: int,
    intensity: str,
    rng: random.Random,
) -> List[SignalLayer]:
    if count <= 0:
        raise ValueError("Layer count must be positive")

    modifier = INTENSITY_MODIFIERS[intensity]
    layers: List[SignalLayer] = []

    for _ in range(count):
        tone = rng.choice(tones)
        image = rng.choice(imagery)
        res = rng.choice(resonance)
        layers.append(
            SignalLayer(
                tone=tone,
                imagery=image,
                resonance=f"{modifier} {res}",
            )
        )

    return layers


def render_signal(layers: Sequence[SignalLayer]) -> str:
    header = (
        "Echo Creative Signal\n"
        f"Timestamp: {datetime.utcnow().isoformat(timespec='seconds')}Z\n"
        f"Layers: {len(layers)}\n"
        "---"
    )
    body = "\n".join(layer.render() for layer in layers)
    return f"{header}\n{body}\n"


def main(argv: Sequence[str] | None = None) -> str:
    args = parse_arguments(argv)

    if args.seed is not None:
        rng = random.Random(args.seed)
    else:
        rng = random.Random()

    tones, imagery, resonance = load_palette(args.palette)
    layers = generate_layers(
        tones=tones,
        imagery=imagery,
        resonance=resonance,
        count=args.layers,
        intensity=args.intensity,
        rng=rng,
    )

    signal = render_signal(layers)
    print(signal)
    return signal


if __name__ == "__main__":
    main()
