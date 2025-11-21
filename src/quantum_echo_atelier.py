"""Quantum Echo Atelier: a novel engine for weaving high-tempo innovation blueprints.

This module constructs "innovation blueprints" by mixing:
- temporal interference between prompt motifs,
- quasi-fractal numeric glyphs derived from trig waves, and
- a narrative stitching pass that produces actionable storylines.

It is intentionally self-contained so it can be imported or executed as a CLI:
```
python -m src.quantum_echo_atelier --prompts "solar sail" "cooperative cities" \
    --constraints "planetary-scale reliability" --output blueprint.json
```
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import pathlib
import random
import statistics
import time
from typing import Iterable, List, Sequence


@dataclasses.dataclass
class IdeaFilament:
    """An atomic motif with resonance metadata."""

    motif: str
    resonance: float
    glyphs: List[float]
    chroma: str


@dataclasses.dataclass
class InnovationBlueprint:
    """A complete, exportable blueprint."""

    title: str
    filaments: List[IdeaFilament]
    novelty_index: float
    interference_score: float
    timestamp: float
    storyline: str
    fingerprint: str

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2)


class QuantumEchoAtelier:
    """Synthesizes motifs into a structured innovation blueprint."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def incubate(
        self, prompts: Sequence[str], constraints: Sequence[str] | None = None
    ) -> InnovationBlueprint:
        if not prompts:
            raise ValueError("At least one prompt is required to incubate a blueprint.")

        constraints = list(constraints or ["open horizon"])
        timestamp = time.time()
        filaments = [self._spin_filament(prompt, timestamp) for prompt in prompts]

        interference = self._interference_pattern(filaments, constraints)
        novelty = self._novelty(filaments, constraints, timestamp)
        storyline = self._stitch_story(filaments, constraints, interference, novelty)
        fingerprint = self._fingerprint(filaments, constraints, timestamp)

        return InnovationBlueprint(
            title=self._title(prompts, constraints),
            filaments=filaments,
            novelty_index=novelty,
            interference_score=interference,
            timestamp=timestamp,
            storyline=storyline,
            fingerprint=fingerprint,
        )

    def export(self, blueprint: InnovationBlueprint, path: str | pathlib.Path) -> pathlib.Path:
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(blueprint.to_json())
        return path

    def _spin_filament(self, prompt: str, timestamp: float) -> IdeaFilament:
        phase = self.random.random() * math.tau
        glyphs = [self._glyph_value(prompt, timestamp, phase + i * 0.83) for i in range(5)]
        resonance = statistics.fmean(glyphs)
        chroma = self._spectral_signature(glyphs)
        return IdeaFilament(motif=prompt, resonance=resonance, glyphs=glyphs, chroma=chroma)

    def _glyph_value(self, prompt: str, timestamp: float, angle: float) -> float:
        prompt_hash = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
        seed = prompt_hash ^ int(timestamp * 1_000_000)
        base = math.sin(angle) + math.cos(angle * 1.618) * 0.5
        jitter = self.random.uniform(-0.2, 0.2)
        scaled = (base + jitter) * (seed % 97) / 42.0
        return round(scaled, 4)

    def _spectral_signature(self, glyphs: Iterable[float]) -> str:
        magnitude = abs(statistics.fmean(glyphs))
        if magnitude < 0.7:
            return "lumen"
        if magnitude < 1.4:
            return "plasma"
        return "aurora"

    def _interference_pattern(
        self, filaments: Sequence[IdeaFilament], constraints: Sequence[str]
    ) -> float:
        constraint_factor = 1 + len(constraints) * 0.07
        overlap = sum(abs(f.resonance) for f in filaments) / max(len(filaments), 1)
        chroma_penalty = 0.1 * len({f.chroma for f in filaments})
        return round(overlap * constraint_factor - chroma_penalty, 4)

    def _novelty(
        self, filaments: Sequence[IdeaFilament], constraints: Sequence[str], timestamp: float
    ) -> float:
        drift = math.sin(timestamp % math.tau) * 0.3
        resonance_entropy = statistics.pstdev(f.resonance for f in filaments) + 0.01
        constraint_entropy = len({c.lower() for c in constraints}) * 0.09
        return round(abs(resonance_entropy + constraint_entropy + drift), 4)

    def _stitch_story(
        self,
        filaments: Sequence[IdeaFilament],
        constraints: Sequence[str],
        interference: float,
        novelty: float,
    ) -> str:
        motifs = ", ".join(f.motif for f in filaments)
        chroma = " / ".join(sorted({f.chroma for f in filaments}))
        constraint_line = "; ".join(constraints)
        return (
            f"Weave {motifs} into a living prototype that honors {constraint_line}. "
            f"Resonance bands: {chroma}. "
            f"Interference amplitude {interference:.2f} fuels a novelty index of {novelty:.2f}."
        )

    def _fingerprint(
        self, filaments: Sequence[IdeaFilament], constraints: Sequence[str], timestamp: float
    ) -> str:
        raw = "|".join(
            [f"{f.motif}:{f.resonance:.4f}:{','.join(map(str, f.glyphs))}" for f in filaments]
            + list(constraints)
            + [str(timestamp)]
        )
        digest = hashlib.sha3_256(raw.encode()).hexdigest()
        return f"QEA-{digest[:16]}"  # short, human-readable fingerprint

    def _title(self, prompts: Sequence[str], constraints: Sequence[str]) -> str:
        motifs = " ∴ ".join(prompts[:3]) + (" …" if len(prompts) > 3 else "")
        return f"Quantum Echo Blueprint · {motifs} ⧉ {len(constraints)} constraint(s)"


def _parse_args() -> tuple[List[str], List[str] | None, str | None, int | None]:
    import argparse

    parser = argparse.ArgumentParser(description="Quantum Echo Atelier")
    parser.add_argument("--prompts", nargs="+", help="Motifs to incubate", required=True)
    parser.add_argument(
        "--constraints",
        nargs="*",
        default=None,
        help="Constraints to honor during the blueprint synthesis",
    )
    parser.add_argument("--output", help="Path to write the blueprint JSON to")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for reproducibility")
    args = parser.parse_args()
    return args.prompts, args.constraints, args.output, args.seed


def main() -> None:
    prompts, constraints, output, seed = _parse_args()
    atelier = QuantumEchoAtelier(seed=seed)
    blueprint = atelier.incubate(prompts=prompts, constraints=constraints)
    if output:
        path = atelier.export(blueprint, output)
        print(f"Blueprint exported to {path}")
    else:
        print(blueprint.to_json())


if __name__ == "__main__":
    main()
