"""The :mod:`echo.grand_crucible` package orchestrates large-scale mythogenic simulations.

This subsystem unifies story architecture, fractal lattice analytics, telemetry, and
artifact persistence into a cohesive orchestration layer.  It is designed to give
other parts of the codebase a high-level interface for constructing audacious
narratives that span thousands of intertwined ritual phases, while remaining fully
deterministic and testable.

The public API mirrors the lifecycle of a grand crucible experiment:

* :class:`~echo.grand_crucible.simulation.GrandCrucible` is the façade for configuring
  and running an experiment.
* :func:`~echo.grand_crucible.cli.run_cli` provides a command-line entrypoint that can
  be wired into existing tooling.
* The :mod:`echo.grand_crucible.storage` module persists artifacts for downstream
  review.

The implementation intentionally favors explicit data modeling and pure functions so
that experiments remain reproducible even when composed of hundreds of phases.
"""

from .simulation import GrandCrucible, GrandCrucibleBuilder
from .cli import run_cli

__all__ = [
    "GrandCrucible",
    "GrandCrucibleBuilder",
    "run_cli",
]
