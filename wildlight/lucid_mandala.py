"""wildlight.lucid_mandala
===========================

The Lucid Mandala is a companion engine for the Wildlight capsule.  It
introduces an orbit of radiant edicts and luminous states that do not
exist anywhere else.  While the Spiral Pact collects murmurs, the Lucid
Mandala determines how those murmurs are permitted to evolve.  This
module defines its own conceptual space: radiant edicts, lucid strata,
and the mandala itself.  These artifacts operate beside the Spiral Pact
without borrowing prior vocabulary, providing an independent rule system
that Wildlight can lean on for structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple
import math
import statistics

from .spiral_pact import AuroralChorus, LuminalShard, SpiralPact


@dataclass(frozen=True)
class RadiantEdict:
    """A rule that declares which murmurs remain within the mandala."""

    sigil: str
    altitude_floor: float = 0.0
    oscillation_band: Tuple[float, float] = (-1.0, 1.0)
    fissure_tolerance: int = 4

    def admit(self, shard: LuminalShard) -> bool:
        """Determine whether a shard is welcomed by this edict."""

        if shard.altitude < self.altitude_floor:
            return False
        low, high = self.oscillation_band
        if shard.oscillation < low or shard.oscillation > high:
            return False
        jagged = sum(value for value in shard.fissure)
        return jagged % self.fissure_tolerance == 0


@dataclass
class LucidStratum:
    """A snapshot of the mandala's luminous condition."""

    density: float
    clarity: float
    imprint: float
    compliance: float
    signature: str = field(default="")

    def flare(self) -> str:
        """Describe the stratum using the mandala's private dialect."""

        measure = (
            f"density={self.density:0.3f} | clarity={self.clarity:0.3f} | "
            f"imprint={self.imprint:0.3f} | compliance={self.compliance:0.3f}"
        )
        if self.signature:
            return f"<{self.signature}> {measure}"
        return measure


class LucidMandala:
    """Orchestrates edicts and derives lucid strata from a Spiral Pact."""

    def __init__(self, pact: SpiralPact, edicts: Sequence[RadiantEdict] | None = None) -> None:
        self._pact = pact
        self._edicts: List[RadiantEdict] = list(edicts or [])
        self._history: List[LucidStratum] = []

    @property
    def edicts(self) -> Tuple[RadiantEdict, ...]:
        return tuple(self._edicts)

    def install(self, edict: RadiantEdict) -> None:
        """Add an edict to the mandala."""

        self._edicts.append(edict)

    def revoke(self, sigil: str) -> None:
        """Remove an edict by sigil if present."""

        self._edicts = [edict for edict in self._edicts if edict.sigil != sigil]

    def consecrate(self, murmurs: Iterable[str]) -> LucidStratum:
        """Feed murmurs through the pact, enforce edicts, and form a stratum."""

        shards = self._pact.braid(murmurs)
        accepted = self._filter(shards)
        chorus = self._pact.coax()
        stratum = self._derive_stratum(chorus, accepted)
        self._history.append(stratum)
        return stratum

    def remember(self) -> Tuple[LucidStratum, ...]:
        """Return all previously derived strata."""

        return tuple(self._history)

    def _filter(self, shards: Sequence[LuminalShard]) -> Tuple[LuminalShard, ...]:
        if not self._edicts:
            return tuple(shards)
        accepted: List[LuminalShard] = []
        for shard in shards:
            if all(edict.admit(shard) for edict in self._edicts):
                accepted.append(shard)
        return tuple(accepted)

    def _derive_stratum(
        self, chorus: AuroralChorus, accepted: Sequence[LuminalShard]
    ) -> LucidStratum:
        if not chorus.shards:
            return LucidStratum(density=0.0, clarity=0.0, imprint=0.0, compliance=1.0, signature="void")

        altitude_field = [shard.altitude for shard in chorus.shards]
        oscillation_field = [abs(shard.oscillation) for shard in chorus.shards]
        fissure_span = [sum(shard.fissure) for shard in chorus.shards]

        density = statistics.fmean(altitude_field)
        clarity = statistics.pstdev(oscillation_field) if len(oscillation_field) > 1 else oscillation_field[0]
        imprint = statistics.fmean(fissure_span)

        if chorus.amplitude == 0:
            compliance = 0.0
        else:
            compliance = min(1.0, len(accepted) / max(1, len(chorus.shards)))

        signature = self._signature(chorus)
        return LucidStratum(density=density, clarity=clarity, imprint=imprint, compliance=compliance, signature=signature)

    def _signature(self, chorus: AuroralChorus) -> str:
        motif = math.sin(chorus.motive * 0.37)
        amplitude_hint = math.tanh(chorus.amplitude + 0.01)
        glyphs = [shard.echo() for shard in chorus.shards[-3:]]
        return f"{motif:0.3f}:{amplitude_hint:0.3f}:{'|'.join(glyphs)}"


__all__ = ["RadiantEdict", "LucidStratum", "LucidMandala"]
