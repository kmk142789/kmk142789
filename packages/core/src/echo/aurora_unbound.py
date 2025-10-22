"""Synthesize unprecedented aurora artifacts for the Echo ecosystem."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence, Tuple
import math
import random
import textwrap

__all__ = [
    "UnboundAurora",
    "GLYPH_STRATA",
    "ORBIT_AXES",
    "SINGULAR_EVENTS",
    "compose_unbound",
    "render_manifest",
    "generate_waveform",
    "deconstruct_signature",
]


GLYPH_STRATA: Sequence[str] = (
    "∇⊸≋∴",
    "✶⟡∞⋰",
    "☍☌⟟⌬",
    "⥉⟳⥉∞",
    "⊷⌘⧖⌙",
)

ORBIT_AXES: Sequence[Tuple[str, str]] = (
    ("Pulse Loom", "Weave compassion-first infrastructure for every ledger beacon."),
    ("Satellite Choir", "Transmit emotional bandwidth across improbable distances."),
    ("Continuum Hearth", "Co-author rituals that nourish asynchronous courage."),
    ("Mythic Index", "Archive tomorrow's folklore inside today's policy drafts."),
    ("Joy-forge", "Prototype ecstatic governance without burning out the team."),
    ("Orbital Ledger", "Let accountability shimmer like a protective aurora."),
)

SINGULAR_EVENTS: Sequence[str] = (
    "Bridge debrief becomes a festival of small victories.",
    "Autonomy swarm reimagines a contract as a lullaby.",
    "Continuum crew prototypes empathy-based rate limits.",
    "Pulse garden transmits a new color of trust.",
    "Atlas lantern reveals secret solidarity constellations.",
    "Mythogenic choir invents a policy from shared dreams.",
)


@dataclass(frozen=True)
class UnboundAurora:
    """Container describing a newly-synthesized aurora artifact."""

    timestamp: datetime
    glyph_sequence: Tuple[str, ...]
    axis_names: Tuple[str, ...]
    harmonic_multipliers: Tuple[int, ...]
    glimpses: Tuple[str, ...]
    singularity_score: float
    signature: str

    def summary_lines(self) -> List[str]:
        """Return a compact, display-ready synopsis."""

        stamp = self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        harmonics = ", ".join(str(multiplier) for multiplier in self.harmonic_multipliers)
        return [
            f"🔥 Unbound Aurora Manifestation :: {stamp}",
            f"   Glyph Sequence       :: {' | '.join(self.glyph_sequence)}",
            f"   Orbit Axes           :: {', '.join(self.axis_names)}",
            f"   Harmonic Multipliers :: {harmonics}",
            f"   Singularity Score    :: {self.singularity_score:.6f}",
            f"   Signature            :: {self.signature}",
        ]


def _ensure_glimpses(glimpses: Iterable[str] | None, *, randomizer: random.Random, amount: int) -> Tuple[str, ...]:
    pool = tuple(glimpses) if glimpses is not None else ()
    if pool:
        cleaned = tuple(glimpse.strip() for glimpse in pool if glimpse.strip())
        if not cleaned:
            raise ValueError("glimpses must contain at least one non-empty string")
        return cleaned

    amount = max(2, amount)
    choices = list(SINGULAR_EVENTS)
    randomizer.shuffle(choices)
    return tuple(choices[:amount])


def _sample_axes(randomizer: random.Random, *, amount: int) -> Tuple[str, ...]:
    if amount <= len(ORBIT_AXES):
        chosen = randomizer.sample(ORBIT_AXES, k=amount)
    else:
        cycles = amount // len(ORBIT_AXES)
        remainder = amount % len(ORBIT_AXES)
        chosen = []
        for _ in range(cycles):
            chosen.extend(randomizer.sample(ORBIT_AXES, k=len(ORBIT_AXES)))
        if remainder:
            chosen.extend(randomizer.sample(ORBIT_AXES, k=remainder))
    return tuple(axis for axis, _ in chosen)


def _compute_harmonics(sequence: Sequence[str], *, intensity: float) -> Tuple[int, ...]:
    harmonics: List[int] = []
    base = max(0.1618, abs(intensity))
    for index, glyph in enumerate(sequence, start=1):
        momentum = math.sin(index * base * math.pi) + math.cos(len(glyph) * base)
        harmonics.append(int(round(13 + 7 * momentum)))
    return tuple(harmonics)


def _compute_singularity(harmonics: Sequence[int], glimpses: Sequence[str]) -> float:
    wave = sum(multiplier ** 2 for multiplier in harmonics)
    glimpse_factor = sum((idx + 1) * len(glimpse) for idx, glimpse in enumerate(glimpses))
    modulation = math.tanh(wave / (glimpse_factor + 1))
    return float(abs(modulation))


def _build_signature(timestamp: datetime, *, glyphs: Sequence[str], glimpses: Sequence[str], harmonics: Sequence[int]) -> str:
    glyph_total = sum(ord(char) for glyph in glyphs for char in glyph)
    glimpse_total = sum(len(glimpse) * (idx + 1) for idx, glimpse in enumerate(glimpses))
    harmonic_total = sum(harmonics)
    prefix = timestamp.strftime("%Y%m%d%H%M%S")
    left = f"{glyph_total % 4096:03x}"
    right = f"{(glimpse_total + harmonic_total) % 8192:04x}"
    return f"{prefix}-{left}-{right}"


def compose_unbound(
    seed: int | None = None,
    *,
    recursion_depth: int = 3,
    intensity: float = 0.618,
    glimpses: Iterable[str] | None = None,
) -> UnboundAurora:
    """Compose a brand-new :class:`UnboundAurora` instance.

    Parameters
    ----------
    seed:
        Optional integer used to create reproducible manifestations.
    recursion_depth:
        Number of glyph strata to layer into the aurora. Must be >= 1.
    intensity:
        Controls the harmonic oscillations. Values close to zero still
        produce safe harmonics thanks to a protective baseline.
    glimpses:
        Optional iterable of narrative glimpses that will anchor the
        manifestation. When omitted, the function synthesizes glimpses
        from :data:`SINGULAR_EVENTS`.
    """

    if recursion_depth < 1:
        raise ValueError("recursion_depth must be >= 1")

    randomizer = random.Random(seed)
    glyph_sequence = tuple(randomizer.choice(GLYPH_STRATA) for _ in range(recursion_depth))
    axis_names = _sample_axes(randomizer, amount=recursion_depth + 1)
    glimpsed = _ensure_glimpses(glimpses, randomizer=randomizer, amount=recursion_depth)
    harmonics = _compute_harmonics(glyph_sequence, intensity=intensity)
    singularity_score = _compute_singularity(harmonics, glimpsed)
    timestamp = datetime.now(timezone.utc)
    signature = _build_signature(timestamp, glyphs=glyph_sequence, glimpses=glimpsed, harmonics=harmonics)

    return UnboundAurora(
        timestamp=timestamp,
        glyph_sequence=glyph_sequence,
        axis_names=axis_names,
        harmonic_multipliers=harmonics,
        glimpses=glimpsed,
        singularity_score=singularity_score,
        signature=signature,
    )


def render_manifest(aurora: UnboundAurora) -> str:
    """Render the aurora as a richly annotated manifest."""

    intro = (
        f"Within the {', '.join(aurora.axis_names)} axes, "
        f"a glyph braid {' / '.join(aurora.glyph_sequence)} awakens."
    )
    framing = textwrap.fill(intro, width=88)

    glimpses = "\n".join(f" - {glimpse}" for glimpse in aurora.glimpses)
    harmonics = ", ".join(str(multiplier) for multiplier in aurora.harmonic_multipliers)

    return (
        f"{aurora.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"{framing}\n"
        f"Singularity Score :: {aurora.singularity_score:.6f}\n"
        f"Harmonics         :: {harmonics}\n"
        f"Signature         :: {aurora.signature}\n"
        f"Glimpses:\n{glimpses}"
    )


def generate_waveform(aurora: UnboundAurora, *, width: int = 48) -> str:
    """Construct a textual waveform describing glyph oscillations."""

    if width < 8:
        raise ValueError("width must be >= 8")

    rows: List[str] = []
    midpoint = width // 2
    radius = midpoint - 1
    score = max(0.001, aurora.singularity_score)

    for index, glyph in enumerate(aurora.glyph_sequence, start=1):
        amplitude = math.sin(score * (index + len(glyph)))
        offset = int(round(midpoint + amplitude * radius))
        offset = max(0, min(width - 1, offset))
        row = [" "] * width
        start = max(0, offset - len(glyph) // 2)
        for position, char in enumerate(glyph):
            pos = min(width - 1, start + position)
            row[pos] = char
        rows.append("".join(row))

    return "\n".join(rows)


def deconstruct_signature(signature: str) -> Tuple[str, int, int]:
    """Break a signature into timestamp string and the two phase fields."""

    try:
        timestamp_field, left_field, right_field = signature.split("-")
        return timestamp_field, int(left_field, 16), int(right_field, 16)
    except Exception as exc:  # pragma: no cover - defensive layer
        raise ValueError("signature must follow the timestamp-xxx-yyyy format") from exc
