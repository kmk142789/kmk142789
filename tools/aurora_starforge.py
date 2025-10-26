"""Aurora Starforge: a cosmic surprise generator.

This module forges shimmering ASCII auroras paired with tiny
micro-myths. It leans on deterministic randomness so that a caller can
recreate a favourite pattern by keeping track of the seed that produced
it. The output is intentionally cinematic while remaining fully inside
ANSI friendly text space.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List


_PALETTE = [".", "*", "+", "✶", "✷", "✸", "✹", "✺", "✻", "✼"]


@dataclass
class AuroraCanvas:
    """Container holding the textual aurora artefact and its metadata."""

    seed: int
    width: int
    height: int
    art: str
    poem: List[str]
    generated_at: datetime

    def as_block(self) -> str:
        """Return the rendered aurora alongside its poem."""

        poem_block = "\n".join(self.poem)
        return f"{self.art}\n\n{poem_block}"


def _wave_value(x: float, y: float, offset: float) -> float:
    """Compute a layered wave field to drive colour intensity."""

    sin_wave = math.sin(x * 0.23 + offset) + math.sin(y * 0.51 - offset * 0.7)
    radial = math.cos(math.hypot(x - 8, y - 3) * 0.18 - offset * 0.3)
    return (sin_wave + radial) / 3.0


def _select_symbol(value: float) -> str:
    """Map a normalised value to a character in the palette."""

    clamped = max(-1.0, min(1.0, value))
    index = int((clamped + 1) / 2 * (len(_PALETTE) - 1))
    return _PALETTE[index]


def _render_rows(width: int, height: int, offset: float) -> Iterable[str]:
    for y in range(height):
        row_symbols = []
        for x in range(width):
            jitter = math.sin((x + y) * 0.11 + offset) * 0.08
            value = _wave_value(x, y, offset) + jitter
            row_symbols.append(_select_symbol(value))
        yield "".join(row_symbols)


def generate_aurora(width: int = 42, height: int = 14, seed: int | None = None) -> AuroraCanvas:
    """Create a shimmering aurora together with a small poem.

    Args:
        width: Number of characters used per row. Must be >= 8.
        height: Number of rows in the aurora. Must be >= 4.
        seed: Optional random seed. If omitted, a random seed is chosen.

    Returns:
        AuroraCanvas: dataclass storing the art, poem, and metadata.

    Raises:
        ValueError: If width or height are below their minimum thresholds.
    """

    if width < 8:
        raise ValueError("Aurora width must be at least 8 characters.")
    if height < 4:
        raise ValueError("Aurora height must be at least 4 rows.")

    rng = random.Random(seed)
    actual_seed = rng.randrange(10**9) if seed is None else seed

    offset = rng.random() * math.pi * 2
    art_rows = list(_render_rows(width, height, offset))
    art = "\n".join(art_rows)

    motifs = [
        "ion trails", "solar murmurs", "tidal echoes", "luminous lattices",
        "celestial gardens", "chronicle sparks", "stellar reveries",
        "quantum embers",
    ]
    subjects = [
        "wanderers", "cartographers", "dreamseeds", "signal keepers",
        "myth weavers", "pulse guardians", "timeborne poets",
    ]
    verbs = [
        "braid", "weave", "kindle", "chart", "gather", "tend", "whisper",
    ]

    poem = [
        f"{rng.choice(motifs).title()} rise over midnight horizons",
        f"where {rng.choice(subjects)} {rng.choice(verbs)} the aurora's vow",
        f"and the cosmos hums: seed {actual_seed:09d}",
    ]

    return AuroraCanvas(
        seed=actual_seed,
        width=width,
        height=height,
        art=art,
        poem=poem,
        generated_at=datetime.utcnow(),
    )


def surprise(seed: int | None = None) -> str:
    """Generate a complete aurora block ready for display."""

    canvas = generate_aurora(seed=seed)
    banner = "∇⊸≋∇  Aurora Starforge  ∇⊸≋∇"
    timestamp = canvas.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    header = f"{banner}\nforged at {timestamp}"
    return f"{header}\n\n{canvas.as_block()}"


if __name__ == "__main__":
    print(surprise())
