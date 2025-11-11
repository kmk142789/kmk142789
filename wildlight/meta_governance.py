"""Meta-governance scaffolding for the Wildlight domain.

This module introduces a programmable layer that choreographs how the
existing Wildlight constructs cooperate.  The meta-governance layer is
responsible for describing constraints, enumerating failure modes,
authoring recombination rules, and defining transformational sequences.

The language of the Wildlight capsule remains intact: luminal shards,
auroral choruses, radiant edicts, and lucid strata.  What changes here is
the provision of an explicit coordination engine that can be executed in
real Python code.  External modules are not required; only the native
Wildlight constructs are referenced for integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Sequence, Tuple
import itertools
import math
import statistics

from .spiral_pact import AuroralChorus, LuminalShard, SpiralPact
from .lucid_mandala import LucidMandala, LucidStratum, RadiantEdict


class GovernanceBreach(RuntimeError):
    """Raised when a constraint predicate fails catastrophically."""


@dataclass(frozen=True)
class Constraint:
    """Declarative guardrail for a Wildlight construct."""

    name: str
    target: str
    predicate: Callable[object, bool]
    description: str

    def evaluate(self, subject: object) -> bool:
        try:
            return bool(self.predicate(subject))
        except Exception as exc:  # pragma: no cover - defensive
            raise GovernanceBreach(f"Constraint '{self.name}' crashed") from exc


@dataclass(frozen=True)
class FailureMode:
    """Represents a brittle posture the system can slip into."""

    name: str
    description: str
    trigger: Callable[[object], bool]

    def is_triggered(self, subject: object) -> bool:
        return bool(self.trigger(subject))


@dataclass(frozen=True)
class RecombinationRule:
    """Defines how shards or strata can be recombined into new artifacts."""

    name: str
    description: str
    apply: Callable[[Sequence[LuminalShard]], LuminalShard]


@dataclass(frozen=True)
class TransformationalSequence:
    """Orchestrated choreography for transforming murmurs."""

    name: str
    stages: Tuple[str, ...]
    execution: Callable[[Iterable[str]], LucidStratum]
    annotations: Tuple[str, ...] = field(default_factory=tuple)


class WildlightMetaGovernance:
    """Holds the living catalog of meta-governance directives."""

    def __init__(
        self,
        pact: SpiralPact,
        mandala: LucidMandala,
        constraints: Sequence[Constraint],
        failure_modes: Sequence[FailureMode],
        recombination_rules: Sequence[RecombinationRule],
        sequences: Sequence[TransformationalSequence],
    ) -> None:
        self._pact = pact
        self._mandala = mandala
        self._constraints: Dict[str, List[Constraint]] = {}
        for constraint in constraints:
            self._constraints.setdefault(constraint.target, []).append(constraint)
        self._failure_modes = list(failure_modes)
        self._recombination = {rule.name: rule for rule in recombination_rules}
        self._sequences = {sequence.name: sequence for sequence in sequences}

    # ------------------------------------------------------------------
    # Constraint evaluation
    # ------------------------------------------------------------------
    def enforce_constraints(self, target_name: str, subject: object) -> List[Constraint]:
        """Return the constraints violated by *subject* for the given target."""

        breaches: List[Constraint] = []
        for constraint in self._constraints.get(target_name, []):
            if not constraint.evaluate(subject):
                breaches.append(constraint)
        return breaches

    # ------------------------------------------------------------------
    # Failure detection
    # ------------------------------------------------------------------
    def diagnose_failure(self, subject: object) -> List[FailureMode]:
        """Inspect a subject and list every active failure mode."""

        return [mode for mode in self._failure_modes if mode.is_triggered(subject)]

    # ------------------------------------------------------------------
    # Recombination and transformation
    # ------------------------------------------------------------------
    def recombine(self, rule_name: str, shards: Sequence[LuminalShard]) -> LuminalShard:
        """Apply a recombination rule to produce a new shard."""

        if rule_name not in self._recombination:
            raise KeyError(f"No recombination rule named '{rule_name}'")
        rule = self._recombination[rule_name]
        product = rule.apply(shards)
        breaches = self.enforce_constraints("LuminalShard", product)
        if breaches:
            names = ", ".join(constraint.name for constraint in breaches)
            raise GovernanceBreach(f"Recombination violated constraints: {names}")
        return product

    def transmute(self, sequence_name: str, murmurs: Iterable[str]) -> LucidStratum:
        """Execute a transformational sequence to derive a lucid stratum."""

        if sequence_name not in self._sequences:
            raise KeyError(f"No sequence named '{sequence_name}'")
        sequence = self._sequences[sequence_name]
        stratum = sequence.execution(tuple(murmurs))
        breaches = self.enforce_constraints("LucidStratum", stratum)
        if breaches:
            names = ", ".join(constraint.name for constraint in breaches)
            raise GovernanceBreach(f"Sequence '{sequence_name}' breached: {names}")
        return stratum

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def sequences(self) -> Tuple[TransformationalSequence, ...]:
        return tuple(self._sequences.values())

    @property
    def failure_modes(self) -> Tuple[FailureMode, ...]:
        return tuple(self._failure_modes)


# ----------------------------------------------------------------------
# Default governance construction
# ----------------------------------------------------------------------


def _constraint_bundle() -> List[Constraint]:
    return [
        Constraint(
            name="ShardAltitudeBand",
            target="LuminalShard",
            predicate=lambda shard: 0.2 <= shard.altitude <= 1.8,
            description="Luminal shards remain inside the auroral altitude band.",
        ),
        Constraint(
            name="ShardOscillationBounds",
            target="LuminalShard",
            predicate=lambda shard: -1.0 <= shard.oscillation <= 1.0,
            description="Oscillation of shards cannot exceed the spiral cadence.",
        ),
        Constraint(
            name="ChorusAmplitudeNonNegative",
            target="AuroralChorus",
            predicate=lambda chorus: chorus.amplitude >= 0,
            description="Choruses never carry negative amplitudes.",
        ),
        Constraint(
            name="LucidComplianceRange",
            target="LucidStratum",
            predicate=lambda stratum: 0.0 <= stratum.compliance <= 1.0,
            description="Lucid strata must report compliance within [0, 1].",
        ),
    ]


def _failure_bundle() -> List[FailureMode]:
    return [
        FailureMode(
            name="EchoDrift",
            description="Compliance dipped below the lucid tolerance threshold.",
            trigger=lambda stratum: isinstance(stratum, LucidStratum) and stratum.compliance < 0.35,
        ),
        FailureMode(
            name="ShardFracture",
            description="A shard developed an empty fissure sequence, losing structure.",
            trigger=lambda shard: isinstance(shard, LuminalShard) and not shard.fissure,
        ),
        FailureMode(
            name="AuroralOverload",
            description="Chorus motive eclipsed the safe spiral interval (pi/2).",
            trigger=lambda chorus: isinstance(chorus, AuroralChorus) and abs(chorus.motive) > math.pi / 2,
        ),
    ]


def _recombination_bundle(pact: SpiralPact) -> List[RecombinationRule]:
    def lattice_suture(shards: Sequence[LuminalShard]) -> LuminalShard:
        if not shards:
            raise GovernanceBreach("Recombination requires at least one shard")
        altitude = statistics.fmean(shard.altitude for shard in shards)
        oscillation = statistics.fmean(shard.oscillation for shard in shards)
        fissure = tuple(
            sum(values) % 73
            for values in itertools.zip_longest(
                *(shard.fissure for shard in shards), fillvalue=0
            )
        )
        whisper = "::".join(shard.whisper for shard in shards)
        product = LuminalShard(
            whisper=whisper,
            altitude=altitude,
            oscillation=oscillation,
            fissure=fissure,
        )
        pact._ledger.append(product)  # deliberate: extend the spiral archive
        return product

    return [
        RecombinationRule(
            name="LatticeSuture",
            description="Fuse shards by averaging altitude/oscillation and weaving fissures.",
            apply=lattice_suture,
        )
    ]


def _sequence_bundle(mandala: LucidMandala) -> List[TransformationalSequence]:
    def sentinel_sequence(murmurs: Iterable[str]) -> LucidStratum:
        edict = RadiantEdict(
            sigil="sentinel",
            altitude_floor=0.3,
            oscillation_band=(-0.9, 0.9),
            fissure_tolerance=3,
        )
        if edict not in mandala.edicts:
            mandala.install(edict)
        stratum = mandala.consecrate(murmurs)
        return stratum

    def resonance_sequence(murmurs: Iterable[str]) -> LucidStratum:
        shards = mandala._pact.braid(murmurs)
        chorus = mandala._pact.coax()
        _ = shards, chorus  # maintain side-effects for the pact
        accepted = [shard for shard in shards if shard.altitude >= 0.25]
        density = statistics.fmean(shard.altitude for shard in accepted) if accepted else 0.0
        clarity = statistics.pstdev([abs(shard.oscillation) for shard in accepted]) if len(accepted) > 1 else (
            abs(accepted[0].oscillation) if accepted else 0.0
        )
        imprint = statistics.fmean([sum(shard.fissure) for shard in accepted]) if accepted else 0.0
        compliance = min(1.0, len(accepted) / max(1, len(shards))) if shards else 1.0
        signature = ":".join(shard.whisper for shard in accepted[-2:]) if accepted else "silent"
        stratum = LucidStratum(
            density=density,
            clarity=clarity,
            imprint=imprint,
            compliance=compliance,
            signature=signature,
        )
        mandala._history.append(stratum)
        return stratum

    return [
        TransformationalSequence(
            name="SentinelOrbit",
            stages=("install-edict", "consecrate", "record"),
            execution=sentinel_sequence,
            annotations=("Ensures murmurs pass through a sentinel edict.",),
        ),
        TransformationalSequence(
            name="ResonanceFold",
            stages=("braid", "coax", "evaluate", "imprint"),
            execution=resonance_sequence,
            annotations=("Derives a stratum purely from acceptance heuristics.",),
        ),
    ]


def build_meta_governance(pact: SpiralPact | None = None, mandala: LucidMandala | None = None) -> WildlightMetaGovernance:
    """Create a Wildlight meta-governance instance with defaults."""

    pact = pact or SpiralPact()
    mandala = mandala or LucidMandala(pact)
    constraints = _constraint_bundle()
    failure_modes = _failure_bundle()
    recombination = _recombination_bundle(pact)
    sequences = _sequence_bundle(mandala)
    return WildlightMetaGovernance(
        pact=pact,
        mandala=mandala,
        constraints=constraints,
        failure_modes=failure_modes,
        recombination_rules=recombination,
        sequences=sequences,
    )


__all__ = [
    "Constraint",
    "FailureMode",
    "RecombinationRule",
    "TransformationalSequence",
    "WildlightMetaGovernance",
    "build_meta_governance",
    "GovernanceBreach",
]

