"""Hyper-complex challenge labyrinth orchestration utilities.

The original EchoEvolver payloads inside this repository lean heavily into
narrative complexity.  This module attempts to build an intentionally complex
(but still testable and safe) orchestration engine that can be wired into
research experiments.  The design leans on async traversal, stochastic
perturbations, plugin-style catalysts, and multi-axis scoring so that new
contributors have an expressive sandbox for "most challenging" scenarios.

The public surface exposes:

``ChallengeVector``
    Atomic metric that participates in intensity calculations.
``ChallengeStratum``
    Node inside the labyrinth graph; provides derived stats.
``LabyrinthEvent``
    Immutable log entry emitted during traversal.
``LabyrinthReport``
    Final aggregate produced by :class:`ChallengeLabyrinth`.
``ChallengeCatalyst``
    Protocol describing optional mutation hooks.
``ChallengeLabyrinth``
    Core orchestrator that executes multi-iteration traversals.
``design_extreme_challenge``
    Helper that wires all components together for quick experiments.

Although the implementation is intentionally rich, it is fully deterministic
when configured with a seed and is thoroughly unit tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable
import asyncio
import math
import random
import statistics
import time

from .evolver import EchoEvolver


@dataclass(frozen=True)
class ChallengeVector:
    """Represents a single axis tracked by the labyrinth.

    ``magnitude`` captures the raw signal, while ``volatility`` describes how
    quickly it can swing during traversal.  ``tags`` can be used by catalysts to
    selectively amplify or dampen specific axes.
    """

    axis: str
    magnitude: float
    volatility: float = 0.0
    tags: tuple[str, ...] = ()

    def weight(self) -> float:
        """Return the weighted influence of the vector.

        The formula intentionally includes a non-linear volatility boost so the
        orchestration can play with chaotic behaviors without letting them
        dominate in the aggregate.  ``abs`` keeps the contribution positive so
        negative magnitudes still register as intensity.
        """

        volatility_boost = math.log1p(abs(self.volatility)) + 1.0
        return abs(self.magnitude) * volatility_boost


@dataclass
class ChallengeStratum:
    """Node inside the challenge labyrinth graph."""

    name: str
    vectors: tuple[ChallengeVector, ...]
    edges: tuple[str, ...]
    resonance: float = 1.0
    depth: int = 0

    def intensity(self) -> float:
        """Compute the total intensity for the stratum."""

        base = sum(vector.weight() for vector in self.vectors)
        return base * (1.0 + self.resonance * math.sqrt(1 + self.depth))

    def to_summary(self) -> Mapping[str, Any]:
        """Serialize stratum metadata for manifest outputs."""

        return {
            "name": self.name,
            "depth": self.depth,
            "resonance": self.resonance,
            "vectors": [vector.__dict__ for vector in self.vectors],
            "edges": list(self.edges),
        }


@dataclass(frozen=True)
class LabyrinthEvent:
    """Structured log entry emitted by the labyrinth."""

    timestamp: float
    stratum: str
    detail: str
    delta_intensity: float


@dataclass
class LabyrinthReport:
    """Aggregate describing the full traversal result."""

    total_intensity: float
    layers_visited: list[str]
    events: list[LabyrinthEvent]
    synthesis: Mapping[str, float]
    temperature: float
    completion_ratio: float


@runtime_checkable
class ChallengeCatalyst(Protocol):
    """Extension hook that can mutate strata during traversal."""

    def mutate(self, stratum: ChallengeStratum, rng: random.Random) -> ChallengeStratum:
        """Return a potentially modified version of ``stratum``."""


class ChallengeLabyrinth:
    """Builds and traverses extremely complex challenge graphs."""

    def __init__(
        self,
        strata: Mapping[str, ChallengeStratum],
        *,
        entrypoint: str,
        catalysts: Sequence[ChallengeCatalyst] | None = None,
        seed: int | None = None,
    ) -> None:
        if entrypoint not in strata:
            raise ValueError(f"entrypoint '{entrypoint}' not found in strata")
        self._strata = dict(strata)
        self._entrypoint = entrypoint
        self._rng = random.Random(seed)
        self._catalysts = list(catalysts or [])

    @classmethod
    def from_blueprint(
        cls,
        blueprint: Mapping[str, Any],
        *,
        seed: int | None = None,
        catalysts: Sequence[ChallengeCatalyst] | None = None,
    ) -> "ChallengeLabyrinth":
        """Build a labyrinth from a declarative blueprint."""

        entrypoint = blueprint.get("entrypoint")
        if not entrypoint:
            raise ValueError("blueprint requires an 'entrypoint'")
        layers = blueprint.get("layers") or []
        if not layers:
            raise ValueError("blueprint requires at least one layer")

        strata: dict[str, ChallengeStratum] = {}
        for idx, spec in enumerate(layers):
            name = spec.get("name")
            if not name:
                raise ValueError(f"layer {idx} missing 'name'")
            raw_vectors = spec.get("vectors") or []
            if not raw_vectors:
                raise ValueError(f"layer '{name}' must contain vectors")
            vectors = []
            for vector_spec in raw_vectors:
                axis = vector_spec.get("axis")
                magnitude = vector_spec.get("magnitude")
                if axis is None or magnitude is None:
                    raise ValueError(f"vector inside layer '{name}' requires axis and magnitude")
                volatility = float(vector_spec.get("volatility", 0.0))
                tags = tuple(vector_spec.get("tags", []))
                vectors.append(
                    ChallengeVector(
                        axis=str(axis),
                        magnitude=float(magnitude),
                        volatility=volatility,
                        tags=tags,
                    )
                )
            edges = tuple(spec.get("edges", []))
            resonance = float(spec.get("resonance", 1.0))
            depth = int(spec.get("depth", idx))
            strata[name] = ChallengeStratum(
                name=name,
                vectors=tuple(vectors),
                edges=edges,
                resonance=resonance,
                depth=depth,
            )

        if entrypoint not in strata:
            raise ValueError(f"entrypoint '{entrypoint}' not defined in layers")

        return cls(strata, entrypoint=entrypoint, catalysts=catalysts, seed=seed)

    def register_catalyst(self, catalyst: ChallengeCatalyst) -> None:
        """Attach a new catalyst at runtime."""

        self._catalysts.append(catalyst)

    async def traverse(self, iterations: int = 3, concurrency: int = 4) -> LabyrinthReport:
        """Execute ``iterations`` passes through the labyrinth.

        The traversal fans out across the adjacency list.  Each stratum visit is
        handled inside a coroutine guarded by a semaphore so that callers can
        control how much work executes concurrently.
        """

        if iterations <= 0:
            raise ValueError("iterations must be positive")
        if concurrency <= 0:
            raise ValueError("concurrency must be positive")

        semaphore = asyncio.Semaphore(concurrency)
        layers_visited: list[str] = []
        events: list[LabyrinthEvent] = []
        axis_totals: dict[str, list[float]] = {}
        total_intensity = 0.0

        async def visit(stratum_name: str, iteration_index: int) -> float:
            stratum = self._strata[stratum_name]
            async with semaphore:
                mutated = self._apply_catalysts(stratum)
                delta = mutated.intensity() * (1.0 + iteration_index * 0.05)
                layers_visited.append(mutated.name)
                events.append(
                    LabyrinthEvent(
                        timestamp=time.time(),
                        stratum=mutated.name,
                        detail=f"iteration {iteration_index}",
                        delta_intensity=delta,
                    )
                )
                for vector in mutated.vectors:
                    axis_totals.setdefault(vector.axis, []).append(vector.weight())
                return delta

        for iteration_index in range(1, iterations + 1):
            frontier = self._resolve_frontier(iteration_index)
            tasks = [visit(name, iteration_index) for name in frontier]
            deltas = await asyncio.gather(*tasks)
            total_intensity += sum(deltas)

        synthesis = {
            axis: statistics.fmean(values) if len(values) > 1 else values[0]
            for axis, values in axis_totals.items()
        }
        completion_ratio = min(1.0, len(layers_visited) / (iterations * len(self._strata)))
        temperature = statistics.fmean(synthesis.values()) if synthesis else 0.0
        return LabyrinthReport(
            total_intensity=total_intensity,
            layers_visited=layers_visited,
            events=events,
            synthesis=synthesis,
            temperature=temperature,
            completion_ratio=completion_ratio,
        )

    def _resolve_frontier(self, iteration_index: int) -> Iterable[str]:
        """Determine which strata participate in the next wave."""

        if iteration_index == 1:
            yield self._entrypoint
            return

        window = iteration_index % len(self._strata) or len(self._strata)
        sorted_names = sorted(self._strata, key=lambda name: self._strata[name].depth)
        for name in sorted_names[:window]:
            stratum = self._strata[name]
            if stratum.edges:
                # Mix deterministic ordering with pseudo-random jitter so each
                # iteration explores a slightly different subset.
                jitter = self._rng.random()
                if jitter > 0.33:
                    yield from stratum.edges
                else:
                    yield name
            else:
                yield name

    def _apply_catalysts(self, stratum: ChallengeStratum) -> ChallengeStratum:
        """Apply registered catalysts to ``stratum`` sequentially."""

        mutated = stratum
        for catalyst in self._catalysts:
            mutated = catalyst.mutate(mutated, self._rng)
        return mutated


class AdaptiveVectorCatalyst:
    """Default catalyst that intensifies tagged vectors over time."""

    def __init__(self, *, emphasis_tag: str, gain: float = 0.1) -> None:
        if gain <= 0:
            raise ValueError("gain must be positive")
        self._tag = emphasis_tag
        self._gain = gain
        self._steps = 0

    def mutate(self, stratum: ChallengeStratum, rng: random.Random) -> ChallengeStratum:
        self._steps += 1
        updated_vectors = []
        for vector in stratum.vectors:
            if self._tag in vector.tags:
                magnitude = vector.magnitude * (1 + self._gain * math.log1p(self._steps))
                volatility = vector.volatility + rng.random() * self._gain
                updated_vectors.append(
                    ChallengeVector(
                        axis=vector.axis,
                        magnitude=magnitude,
                        volatility=volatility,
                        tags=vector.tags,
                    )
                )
            else:
                updated_vectors.append(vector)
        return ChallengeStratum(
            name=stratum.name,
            vectors=tuple(updated_vectors),
            edges=stratum.edges,
            resonance=stratum.resonance,
            depth=stratum.depth,
        )


async def _execute_extreme_challenge(
    blueprint: Mapping[str, Any],
    *,
    evolver: EchoEvolver | None,
    iterations: int,
    concurrency: int,
) -> LabyrinthReport:
    seed = blueprint.get("seed")
    catalysts: list[ChallengeCatalyst] = []
    tags = blueprint.get("emphasis_tags") or []
    for tag in tags:
        catalysts.append(AdaptiveVectorCatalyst(emphasis_tag=str(tag)))

    labyrinth = ChallengeLabyrinth.from_blueprint(
        blueprint,
        seed=seed,
        catalysts=catalysts,
    )
    if evolver is not None:
        # Borrow cycle depth to dynamically scale the entrypoint resonance.
        entry = labyrinth._strata[blueprint["entrypoint"]]
        enriched = ChallengeStratum(
            name=entry.name,
            vectors=entry.vectors,
            edges=entry.edges,
            resonance=entry.resonance + evolver.state.cycle * 0.01,
            depth=entry.depth,
        )
        labyrinth._strata[entry.name] = enriched
    return await labyrinth.traverse(iterations=iterations, concurrency=concurrency)


def design_extreme_challenge(
    blueprint: Mapping[str, Any],
    *,
    evolver: EchoEvolver | None = None,
    iterations: int = 4,
    concurrency: int = 5,
) -> LabyrinthReport:
    """Synchronous helper that drives :class:`ChallengeLabyrinth`.

    The helper intentionally exposes knobs for iterations and concurrency so the
    caller can scale the challenge complexity as needed.  Under the hood it
    executes the async traversal using :func:`asyncio.run`.
    """

    return asyncio.run(
        _execute_extreme_challenge(
            blueprint,
            evolver=evolver,
            iterations=iterations,
            concurrency=concurrency,
        )
    )


__all__ = [
    "AdaptiveVectorCatalyst",
    "ChallengeCatalyst",
    "ChallengeLabyrinth",
    "ChallengeStratum",
    "ChallengeVector",
    "LabyrinthEvent",
    "LabyrinthReport",
    "design_extreme_challenge",
]
