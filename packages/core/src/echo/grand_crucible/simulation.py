"""Grand crucible orchestration logic."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

from . import blueprint as blueprint_module
from .blueprint import Blueprint
from .lattice import build_lattice
from .storycraft import build_phase_heatmap, craft_blueprint_overview, render_heatmap_ascii, storyline_from_lattice
from .storage import write_composite_artifact
from .telemetry import TelemetrySnapshot, capture_blueprint_metrics


@dataclass
class GrandCrucibleArtifacts:
    """Artifacts produced by running the crucible."""

    overview: str
    heatmap: str
    storyline: List[str]
    telemetry: TelemetrySnapshot

    def persist(self, directory: Path) -> None:
        """Persist all artifacts to the target directory."""

        write_composite_artifact(
            directory,
            overview=self.overview,
            heatmap=self.heatmap,
            storyline=self.storyline,
            telemetry=self.telemetry,
        )


@dataclass
class GrandCrucible:
    """Executes a grand crucible experiment."""

    blueprint: Blueprint
    observers: Sequence[Callable[[GrandCrucibleArtifacts], None]] = field(default_factory=list)

    def run(self) -> GrandCrucibleArtifacts:
        """Run the crucible and return the resulting artifacts."""

        self.blueprint.validate()
        lattice = build_lattice(self.blueprint)
        overview = craft_blueprint_overview(self.blueprint, lattice)
        heatmap = render_heatmap_ascii(build_phase_heatmap(self.blueprint))
        storyline = storyline_from_lattice(lattice)
        telemetry = capture_blueprint_metrics(self.blueprint, lattice)
        artifacts = GrandCrucibleArtifacts(
            overview=overview,
            heatmap=heatmap,
            storyline=storyline,
            telemetry=telemetry,
        )
        for observer in self.observers:
            observer(artifacts)
        return artifacts


class GrandCrucibleBuilder:
    """Builder for :class:`GrandCrucible`."""

    def __init__(self):
        self._blueprint: Optional[Blueprint] = None
        self._observers: List[Callable[[GrandCrucibleArtifacts], None]] = []

    def with_blueprint(self, blueprint: Blueprint) -> "GrandCrucibleBuilder":
        self._blueprint = blueprint
        return self

    def with_default_blueprint(self) -> "GrandCrucibleBuilder":
        self._blueprint = blueprint_module.build_default_blueprint()
        return self

    def add_observer(self, observer: Callable[[GrandCrucibleArtifacts], None]) -> "GrandCrucibleBuilder":
        self._observers.append(observer)
        return self

    def build(self) -> GrandCrucible:
        if self._blueprint is None:
            raise ValueError("Blueprint must be provided before building a GrandCrucible")
        return GrandCrucible(blueprint=self._blueprint, observers=tuple(self._observers))


def run_and_persist(
    *,
    blueprint: Optional[Blueprint] = None,
    output_directory: Optional[Path] = None,
    observers: Optional[Iterable[Callable[[GrandCrucibleArtifacts], None]]] = None,
) -> GrandCrucibleArtifacts:
    """Convenience helper that runs the crucible and persists artifacts."""

    builder = GrandCrucibleBuilder()
    if blueprint is not None:
        builder.with_blueprint(blueprint)
    else:
        builder.with_default_blueprint()

    if observers:
        for observer in observers:
            builder.add_observer(observer)

    crucible = builder.build()
    artifacts = crucible.run()
    if output_directory:
        artifacts.persist(output_directory)
    return artifacts
