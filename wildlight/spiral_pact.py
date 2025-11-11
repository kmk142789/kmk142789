"""wildlight.spiral_pact
=================================

The Spiral Pact is an entirely new conceptual instrument born from
unmapped intuition.  It interprets strings as luminous murmurs and folds
those murmurs into a swirling archive of "luminal shards".  Each shard
captures altitude, oscillation, and a fractured residue derived from the
relative posture of the utterance.  The pact subsequently braids the
shards into a chorus-like lattice called an :class:`AuroralChorus` that
can be rendered into a textual aurora.

None of these constructs have appeared elsewhere in this repository.
They stand apart from established modules, subsystems, or naming
patterns, offering a spontaneous-yet-coherent feature for exploring
improvised conceptual dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence
import math
import random
import statistics
import textwrap


@dataclass
class LuminalShard:
    """A fragment of sonic light captured from an utterance.

    Parameters
    ----------
    whisper:
        The original utterance distilled into its gentle resonance.
    altitude:
        A floating point indication of how high the fragment rose during
        capture.  Values are normalized around ``1.0``.
    oscillation:
        A sinusoidal coefficient representing the shard's rhythmic sway.
    fissure:
        A short sequence of integer residues extracted from the cadence
        of the utterance.  The fissure expresses the shard's hidden
        fracture geometry.
    """

    whisper: str
    altitude: float
    oscillation: float
    fissure: Sequence[int] = field(default_factory=list)

    def echo(self) -> str:
        """Return a concise representation for narrative weaving."""

        crest = f"{self.altitude:0.3f}@{self.oscillation:0.3f}"
        residues = "-".join(f"{value:02d}" for value in self.fissure) or "--"
        return f"<{self.whisper}|{crest}|{residues}>"


@dataclass
class AuroralChorus:
    """A shimmering braid of luminal shards.

    The chorus can be rendered into a textual aurora that visualizes the
    cumulative geometry of the shards.  Rendering is intentionally
    playful yet deterministic given a consistent shard sequence.
    """

    shards: Sequence[LuminalShard]
    motive: float
    amplitude: float

    def render(self, width: int = 52) -> str:
        """Render the auroral chorus as a textual panorama."""

        if not self.shards:
            return "(silent aurora)"

        pad = max(3, width)
        lines: List[str] = []
        motif = math.sin(self.motive) * 0.5 + 0.5
        for shard in self.shards:
            glimmer = motif * shard.altitude * (abs(shard.oscillation) + 0.2)
            depth = min(pad - 1, max(0, int(glimmer * pad)))
            silhouette = " " * depth + "✧" + " " * (pad - depth - 1)
            lines.append(silhouette.rstrip())

        cadence = "\n".join(lines)
        fissure_cloud = ", ".join(
            "".join(chr(0x1F300 + (value % 16)) for value in shard.fissure)
            for shard in self.shards
        ) or ""
        footer = textwrap.fill(
            f"Amplitude: {self.amplitude:0.3f} | Motive: {self.motive:0.3f}"
            f" | Fissure Cloud: {fissure_cloud}",
            width=width,
        )
        return cadence + "\n" + footer


class SpiralPact:
    """Curates luminal shards and braids them into an auroral chorus."""

    def __init__(self, spark: float | None = None) -> None:
        self._spark = spark if spark is not None else random.random() + 0.618
        self._ledger: List[LuminalShard] = []
        self._invocation = 0

    def capture(self, utterance: str) -> LuminalShard:
        """Capture a single utterance as a luminal shard."""

        base = sum(ord(ch) for ch in utterance) or 1
        height = math.tanh(base / 512.0) + (self._spark * 0.05)
        sway = math.sin(base * self._spark * 0.37)
        fissure = tuple((ord(ch) * (idx + 1)) % 73 for idx, ch in enumerate(utterance[:5]))
        shard = LuminalShard(whisper=utterance, altitude=height, oscillation=sway, fissure=fissure)
        self._ledger.append(shard)
        self._invocation += 1
        return shard

    def braid(self, murmurs: Iterable[str]) -> List[LuminalShard]:
        """Capture multiple murmurs in sequence."""

        return [self.capture(murmur) for murmur in murmurs]

    def coax(self) -> AuroralChorus:
        """Form an auroral chorus from the current ledger."""

        motive = (self._spark * self._invocation) + statistics.fmean(
            (abs(shard.oscillation) + shard.altitude) for shard in self._ledger
        ) if self._ledger else self._spark
        amplitude = statistics.pstdev(
            [shard.altitude for shard in self._ledger]
        ) if len(self._ledger) > 1 else self._spark * 0.13
        return AuroralChorus(shards=tuple(self._ledger), motive=motive, amplitude=amplitude)

    def forget(self) -> None:
        """Release all captured shards back into the ether."""

        self._ledger.clear()
        self._invocation = 0


__all__ = ["LuminalShard", "AuroralChorus", "SpiralPact"]
