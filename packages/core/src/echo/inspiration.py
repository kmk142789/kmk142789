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


@dataclass
class ImaginationPhase:
    """Represent a single phase of an imagination sequence."""

    index: int
    spark: str
    resonance: float
    vector: str

    def to_dict(self) -> dict[str, object]:
        """Serialise the phase to a JSON compatible dictionary."""

        return {
            "index": self.index,
            "spark": self.spark,
            "resonance": self.resonance,
            "vector": self.vector,
        }


@dataclass
class ImaginationSequence:
    """A multi-phase creative expansion derived from inspiration sparks."""

    theme: str
    phases: List[ImaginationPhase]
    seed: Optional[int] = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON compatible representation of the sequence."""

        payload: dict[str, object] = {
            "theme": self.theme,
            "phases": [phase.to_dict() for phase in self.phases],
        }
        if self.seed is not None:
            payload["seed"] = self.seed
        return payload

    def to_markdown(self) -> str:
        """Render the sequence as a Markdown narrative."""

        lines: List[str] = [f"# Imagination sequence for {self.theme}", ""]
        for phase in self.phases:
            lines.extend(
                [
                    f"## Phase {phase.index}",
                    f"- spark: {phase.spark}",
                    f"- resonance: {phase.resonance:.2f}",
                    f"- vector: {phase.vector}",
                    "",
                ]
            )
        if self.seed is not None:
            lines.append(f"> seeded with {self.seed}")
        # Ensure the output ends with a newline for readability.
        return "\n".join(lines).rstrip() + "\n"


def weave_imagination_sequence(
    theme: str,
    *,
    horizons: int = 3,
    intensity: float = 0.85,
    rng_seed: Optional[int] = None,
) -> ImaginationSequence:
    """Expand a theme into a multi-phase imagination journey.

    The function builds upon :func:`forge_inspiration` to cultivate a series of
    sparks that grow in resonance. Each phase is deterministic when ``rng_seed``
    is supplied, enabling reproducible creative experiments.

    Parameters
    ----------
    theme:
        Base motif guiding the imagination sequence. Blank values default to
        ``"Echo"``.
    horizons:
        Number of phases to generate. Must be a positive integer.
    intensity:
        Starting resonance intensity between ``0`` and ``1`` (inclusive). Values
        closer to ``1`` begin at a higher resonance.
    rng_seed:
        Optional seed ensuring deterministic output.
    """

    if horizons <= 0:
        raise ValueError("horizons must be a positive integer")
    if not (0.0 < intensity <= 1.0):
        raise ValueError("intensity must be between 0 and 1 inclusive")

    theme_text = theme.strip() or "Echo"
    rng = Random(rng_seed)

    vector_templates = [
        "Chart the {motif} orbit of {theme}",
        "Refract {theme}'s promise through the {motif}",
        "Echo the {motif} rising within {theme}",
        "Illuminate {theme} via a {motif} compass",
        "Stitch {theme} to the {motif} horizon",
        "Transpose {theme} along the {motif} bridge",
    ]
    motifs = [
        "mythogenic pulse",
        "aurora lattice",
        "wildfire memory",
        "luminous archive",
        "sovereign cadence",
        "tide of possibilities",
        "continuum bloom",
        "resonance canopy",
    ]

    phases: List[ImaginationPhase] = []

    if horizons == 1:
        resonance_values = [round(intensity, 3)]
    else:
        step = (1.0 - intensity) / (horizons - 1)
        resonance_values = [round(intensity + step * i, 3) for i in range(horizons)]

    for index in range(1, horizons + 1):
        spark_seed = rng.randint(0, 10**9)
        spark = forge_inspiration(theme_text, lines=1, rng_seed=spark_seed).sparks[0]
        motif = rng.choice(motifs)
        vector_template = rng.choice(vector_templates)
        vector = vector_template.format(theme=theme_text, motif=motif)
        resonance_value = resonance_values[index - 1]

        phases.append(
            ImaginationPhase(
                index=index,
                spark=spark,
                resonance=resonance_value,
                vector=vector,
            )
        )

    return ImaginationSequence(theme=theme_text, phases=phases, seed=rng_seed)

