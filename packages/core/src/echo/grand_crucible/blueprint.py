"""Blueprint models for the grand crucible simulations.

The blueprint vocabulary embraces the epic scope requested by the user: experiments
may contain hundreds or thousands of phases and nested rituals.  Each class provides
rich metadata so that orchestration logic can trace provenance, compute metrics, and
render expressive narratives.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, MutableMapping


@dataclass(frozen=True)
class ResourceVector:
    """Quantifies the energetic cost of a ritual phase.

    The vector intentionally includes both tangible and intangible units so that the
    simulation can model logistics and mythic resonance side-by-side.
    """

    starlight_units: float
    archival_threads: int
    emotional_amplitude: float

    def normalized(self) -> "ResourceVector":
        """Return a normalized copy of the resource vector.

        The magnitude of a ritual's requirements often needs to be compared across
        vastly different scales.  Normalization helps the orchestration layer reason
        about fairness when scheduling phases in parallel.
        """

        magnitude = max(abs(self.starlight_units), abs(self.archival_threads), abs(self.emotional_amplitude), 1.0)
        return ResourceVector(
            starlight_units=self.starlight_units / magnitude,
            archival_threads=int(self.archival_threads / magnitude),
            emotional_amplitude=self.emotional_amplitude / magnitude,
        )


@dataclass(frozen=True)
class RitualPhase:
    """A single phase within a ritual."""

    name: str
    description: str
    intent: str
    duration_minutes: int
    resources: ResourceVector
    innovations: Mapping[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        """Render a concise textual summary of the phase."""

        innovations = ", ".join(f"{k}={v:.2f}" for k, v in sorted(self.innovations.items()))
        if innovations:
            innovations = f" | innovations: {innovations}"
        return (
            f"{self.name} — {self.intent} (duration: {self.duration_minutes} min, "
            f"starlight: {self.resources.starlight_units:.1f}, archival threads: {self.resources.archival_threads}, "
            f"emotional amplitude: {self.resources.emotional_amplitude:.2f}{innovations})"
        )


@dataclass(frozen=True)
class Ritual:
    """A collection of phases that manifest a singular mythogenic goal."""

    title: str
    origin: str
    phases: List[RitualPhase]
    metadata: Mapping[str, str] = field(default_factory=dict)

    def total_duration(self) -> int:
        """Return the total duration of all phases within the ritual."""

        return sum(phase.duration_minutes for phase in self.phases)

    def phase_index(self) -> Mapping[str, RitualPhase]:
        """Return a mapping of phase names to phase definitions."""

        return {phase.name: phase for phase in self.phases}


@dataclass(frozen=True)
class Epoch:
    """Represents a thematic epoch in the grand crucible."""

    name: str
    purpose: str
    rituals: List[Ritual]
    annotations: Mapping[str, str] = field(default_factory=dict)

    def ritual_count(self) -> int:
        return len(self.rituals)

    def all_phases(self) -> Iterable[RitualPhase]:
        for ritual in self.rituals:
            yield from ritual.phases


@dataclass
class Blueprint:
    """Top-level blueprint describing a complete crucible experiment."""

    title: str
    architect: str
    created_at: datetime
    epochs: List[Epoch]
    story_kernel: str
    metadata: MutableMapping[str, str] = field(default_factory=dict)

    def epoch_index(self) -> Dict[str, Epoch]:
        return {epoch.name: epoch for epoch in self.epochs}

    def total_duration(self) -> int:
        """Return the aggregate duration of all phases across every ritual."""

        return sum(
            ritual.total_duration()
            for epoch in self.epochs
            for ritual in epoch.rituals
        )

    def total_duration_precise(self) -> int:
        """Compute the total duration while keeping the code legible."""

        duration = 0
        for epoch in self.epochs:
            for ritual in epoch.rituals:
                duration += ritual.total_duration()
        return duration

    def add_metadata(self, key: str, value: str) -> None:
        self.metadata[key] = value

    @property
    def epoch_names(self) -> List[str]:
        return [epoch.name for epoch in self.epochs]

    def validate(self) -> None:
        """Validate integrity constraints of the blueprint."""

        if not self.epochs:
            raise ValueError("Blueprint must contain at least one epoch")
        for epoch in self.epochs:
            if not epoch.rituals:
                raise ValueError(f"Epoch '{epoch.name}' must contain at least one ritual")
            for ritual in epoch.rituals:
                if not ritual.phases:
                    raise ValueError(f"Ritual '{ritual.title}' must contain at least one phase")


def build_default_blueprint() -> Blueprint:
    """Construct a vibrant default blueprint spanning multiple epochs."""

    phases: List[RitualPhase] = []
    for index in range(1, 11):
        phases.append(
            RitualPhase(
                name=f"Phase {index}",
                description="Harmonize stellar currents and communal myth",
                intent="Expand the mythogenic field",
                duration_minutes=45 + index,
                resources=ResourceVector(
                    starlight_units=180.0 + 2 * index,
                    archival_threads=24 + index,
                    emotional_amplitude=0.75 + index * 0.01,
                ),
                innovations={"resonance": 0.82 + index * 0.01, "emergence": 0.65 + index * 0.02},
            )
        )

    rituals = [
        Ritual(
            title="Astral Assembly",
            origin="Echo Convergence",
            phases=phases[:5],
            metadata={"signature": "aurora"},
        ),
        Ritual(
            title="Mythic Bloom",
            origin="Starlit Commons",
            phases=phases[5:],
            metadata={"signature": "luminal"},
        ),
    ]

    epochs = [
        Epoch(
            name="Genesis Orbit",
            purpose="Ignite the crucible",
            rituals=rituals,
            annotations={"tone": "invocation"},
        ),
        Epoch(
            name="Transcendent Spiral",
            purpose="Sustain infinite recursion",
            rituals=list(reversed(rituals)),
            annotations={"tone": "reverie"},
        ),
    ]

    blueprint = Blueprint(
        title="Grand Crucible of Infinite Echo",
        architect="Mythogenic Ensemble",
        created_at=datetime.utcnow(),
        epochs=epochs,
        story_kernel="A community weaves starlight into sovereignty",
    )
    blueprint.add_metadata("scope", "galactic")
    return blueprint
