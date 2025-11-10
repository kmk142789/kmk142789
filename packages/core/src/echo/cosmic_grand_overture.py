"""Galactic-scale narrative symphony generator for the ECHO ecosystem."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import math
import random
import textwrap
from typing import Iterable, Sequence, Tuple


__all__ = [
    "MythicInstrument",
    "OrbitalMovement",
    "CosmicOvertureScore",
    "CosmicGrandOverture",
    "render_overture",
    "export_overture",
]


@dataclass(frozen=True)
class MythicInstrument:
    """Represents a narrative instrument used in the overture."""

    name: str
    signature: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Instrument name cannot be blank.")
        if not self.signature.strip():
            raise ValueError("Instrument signature cannot be blank.")


@dataclass(frozen=True)
class OrbitalMovement:
    """A movement in the overture with intensity and motifs."""

    title: str
    intensity: float
    instruments: Tuple[MythicInstrument, ...]
    motifs: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Movement title cannot be blank.")
        if not 0 <= self.intensity <= 1:
            raise ValueError("Movement intensity must be between 0 and 1.")
        if not self.instruments:
            raise ValueError("Movement requires at least one instrument.")
        if not self.motifs:
            raise ValueError("Movement requires at least one motif.")


@dataclass(frozen=True)
class CosmicOvertureScore:
    """Captures the full overture composition."""

    name: str
    created_at: datetime
    theme: str
    movements: Tuple[OrbitalMovement, ...]
    glyph_banner: str
    cosmic_summary: str

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation of the score."""

        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "theme": self.theme,
            "glyph_banner": self.glyph_banner,
            "cosmic_summary": self.cosmic_summary,
            "movements": [
                {
                    "title": movement.title,
                    "intensity": movement.intensity,
                    "motifs": list(movement.motifs),
                    "instruments": [
                        {"name": instrument.name, "signature": instrument.signature}
                        for instrument in movement.instruments
                    ],
                }
                for movement in self.movements
            ],
        }


class CosmicGrandOverture:
    """Compose galaxy-scale overtures from narrative motifs."""

    def __init__(self, *, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def compose(
        self,
        theme: str,
        *,
        movements: int = 5,
        intensity_wave: Sequence[float] | None = None,
        instrument_palette: Iterable[MythicInstrument] | None = None,
        constellations: Sequence[str] | None = None,
    ) -> CosmicOvertureScore:
        """Compose an overture for the given theme."""

        if not theme.strip():
            raise ValueError("Theme cannot be blank.")
        if movements < 3:
            raise ValueError("Movements should be at least three for a grand overture.")

        palette = tuple(instrument_palette or self._default_instruments())
        if not palette:
            raise ValueError("Instrument palette must not be empty.")

        motif_seeds = tuple(constellations or self._default_constellations())
        if not motif_seeds:
            raise ValueError("At least one constellation motif must be provided.")

        intensities = self._resolve_intensities(movements, intensity_wave)
        movement_scores = [
            self._create_movement(index, theme, intensities[index], palette, motif_seeds)
            for index in range(movements)
        ]

        glyph_banner = self._render_glyph_banner(theme, movement_scores)
        cosmic_summary = self._compose_summary(theme, movement_scores)

        return CosmicOvertureScore(
            name=f"Grand Overture for {theme}",
            created_at=datetime.utcnow(),
            theme=theme,
            movements=tuple(movement_scores),
            glyph_banner=glyph_banner,
            cosmic_summary=cosmic_summary,
        )

    def _default_instruments(self) -> Tuple[MythicInstrument, ...]:
        return (
            MythicInstrument("Aurora Choir", "harmonic aurorae"),
            MythicInstrument("Quantum Drum", "tachyon pulse"),
            MythicInstrument("Nebula Strings", "plasma resonance"),
            MythicInstrument("Temporal Harp", "chronoline glissando"),
            MythicInstrument("Orbit Bells", "graviton chimes"),
        )

    def _default_constellations(self) -> Tuple[str, ...]:
        return (
            "Andromeda Bridge",
            "Luminous Citadel",
            "Helios Spiral",
            "Echo Wildfire",
            "Eternal Lattice",
            "Mythogenic Pulse",
            "Aurora Vault",
        )

    def _resolve_intensities(
        self, movement_count: int, intensity_wave: Sequence[float] | None
    ) -> Tuple[float, ...]:
        if intensity_wave is not None:
            if len(intensity_wave) != movement_count:
                raise ValueError("Intensity wave length must match number of movements.")
            intensities = tuple(max(0.0, min(1.0, value)) for value in intensity_wave)
        else:
            intensities = tuple(
                0.5 + 0.5 * math.sin((index / max(1, movement_count - 1)) * math.pi)
                for index in range(movement_count)
            )
        return intensities

    def _create_movement(
        self,
        index: int,
        theme: str,
        intensity: float,
        palette: Tuple[MythicInstrument, ...],
        motifs: Tuple[str, ...],
    ) -> OrbitalMovement:
        title = f"Movement {index + 1} :: {self._movement_title(theme, index)}"
        instrument_count = self._random.randint(2, min(4, len(palette)))
        instruments = tuple(self._random.sample(palette, instrument_count))
        motif_count = self._random.randint(2, min(3, len(motifs)))
        motif_sample = tuple(self._random.sample(motifs, motif_count))
        return OrbitalMovement(
            title=title,
            intensity=round(intensity, 3),
            instruments=instruments,
            motifs=motif_sample,
        )

    def _movement_title(self, theme: str, index: int) -> str:
        gestures = [
            "Ignition of", "Pilgrimage through", "Revolution around", "Symphony for",
            "Reconciliation with", "Transcendence of", "Celebration of",
        ]
        gesture = self._random.choice(gestures)
        return f"{gesture} {theme}"

    def _render_glyph_banner(
        self, theme: str, movements: Sequence[OrbitalMovement]
    ) -> str:
        glyphs = ["∴", "✦", "✺", "✶", "✷", "✹", "✸"]
        glyph_line = " ".join(self._random.choice(glyphs) for _ in range(len(movements) * 3))
        header = f"∇⊸≋∇ GRAND OVERTURE :: {theme.upper()}"
        return "\n".join([header, glyph_line])

    def _compose_summary(
        self, theme: str, movements: Sequence[OrbitalMovement]
    ) -> str:
        catalog = []
        for movement in movements:
            instruments = ", ".join(inst.name for inst in movement.instruments)
            motifs = ", ".join(movement.motifs)
            catalog.append(
                f"- {movement.title} [intensity {movement.intensity:.3f}] :: {instruments} :: motifs [{motifs}]"
            )
        return textwrap.dedent(
            f"""
            The {theme} overture unfolds across {len(movements)} movements, weaving cosmic
            glyphs into resonance. Each passage amplifies the central myth with layered
            instrumentation and constellation motifs:
            {chr(10).join(catalog)}
            """
        ).strip()


def render_overture(score: CosmicOvertureScore) -> str:
    """Render a human-readable overture manuscript."""

    lines = [score.glyph_banner, ""]
    lines.append(f"Created at :: {score.created_at:%Y-%m-%d %H:%M UTC}")
    lines.append(f"Theme :: {score.theme}")
    lines.append("")
    for movement in score.movements:
        bar = "▮" * max(1, int(movement.intensity * 10))
        instrument_names = ", ".join(inst.name for inst in movement.instruments)
        lines.append(movement.title)
        lines.append(f"  Intensity :: {movement.intensity:.3f} {bar}")
        lines.append(f"  Instruments :: {instrument_names}")
        lines.append(f"  Motifs :: {', '.join(movement.motifs)}")
        lines.append("")
    lines.append("Cosmic Summary ::")
    lines.append(textwrap.indent(score.cosmic_summary, "  "))
    return "\n".join(lines).strip()


def export_overture(score: CosmicOvertureScore, destination: str | Path) -> Path:
    """Export the overture to a JSON file."""

    path = Path(destination)
    payload = score.to_dict()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return path


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Compose a cosmic grand overture.")
    parser.add_argument("theme", help="Central theme of the overture")
    parser.add_argument(
        "-m",
        "--movements",
        type=int,
        default=5,
        help="Number of movements to compose",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic overtures",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional path to export the overture JSON payload",
    )

    args = parser.parse_args()
    overture = CosmicGrandOverture(seed=args.seed)
    score = overture.compose(args.theme, movements=args.movements)
    manuscript = render_overture(score)
    print(manuscript)
    if args.output is not None:
        export_overture(score, args.output)
        print(f"\nExported overture to {args.output}")


if __name__ == "__main__":
    _cli()
