"""Command-line interface for running EchoEvolver cycles.

This helper mirrors the canonical :meth:`echo.evolver.EchoEvolver.run`
routine and exposes the most common toggles as command-line flags.  It
exists so developers (and curious operators) can evolve the system with a
single invocation without needing to remember the Python API surface.  The
CLI intentionally keeps the behaviour deterministic when a ``--seed`` is
provided which makes automated pipelines and tests easier to reproduce.

The original helper only supported a single cycle which meant operators
needing to evolve several steps in succession had to orchestrate repeated
invocations manually.  The modern interface therefore adds ``--cycles`` and
``--persist-intermediate`` controls so the entire cadence can be described
in one command while still keeping deterministic runs for tests.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterable, Optional

from echo.evolver import EchoEvolver


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the evolve-system CLI."""

    parser = argparse.ArgumentParser(
        prog="evolve-system",
        description="Run a full EchoEvolver cycle with optional controls.",
    )
    parser.add_argument(
        "--enable-network",
        action="store_true",
        help=(
            "Include propagation events that describe live network intent. "
            "All actions remain simulated for safety, mirroring the Python API."
        ),
    )
    parser.add_argument(
        "--no-persist-artifact",
        action="store_true",
        help="Skip writing the cycle artifact to disk.",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help=(
            "Optional path for the persisted artifact.  When omitted the evolver "
            "uses its internal default location."
        ),
    )
    parser.add_argument(
        "--eden88-theme",
        default=None,
        help="Override the theme used by Eden88 when crafting the sanctuary artifact.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed value for the evolver RNG.  When omitted a random seed is used.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of sequential cycles to run in a single invocation (default: 1).",
    )
    parser.add_argument(
        "--persist-intermediate",
        action="store_true",
        help=(
            "Persist artifacts after every cycle when running multiple cycles. "
            "Ignored when the final artifact is skipped."
        ),
    )
    return parser


def create_evolver(*, seed: Optional[int], artifact: Optional[Path]) -> EchoEvolver:
    """Instantiate :class:`EchoEvolver` with optional overrides."""

    rng = random.Random(seed) if seed is not None else None
    artifact_path = artifact if artifact is None else Path(artifact)
    return EchoEvolver(rng=rng, artifact_path=artifact_path)


def execute_evolution(
    *,
    enable_network: bool,
    persist_artifact: bool,
    eden88_theme: Optional[str],
    seed: Optional[int],
    artifact: Optional[Path],
    cycles: int,
    persist_intermediate: bool,
) -> EchoEvolver:
    """Execute a full cycle and return the configured evolver instance."""

    evolver = create_evolver(seed=seed, artifact=artifact)
    if cycles <= 0:
        raise ValueError("cycles must be a positive integer")

    if cycles == 1:
        evolver.run(
            enable_network=enable_network,
            persist_artifact=persist_artifact,
            eden88_theme=eden88_theme,
        )
    else:
        evolver.run_cycles(
            cycles,
            enable_network=enable_network,
            persist_artifact=persist_artifact,
            persist_intermediate=persist_intermediate,
            eden88_theme=eden88_theme,
        )
    return evolver


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry-point for the evolve-system command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    persist_artifact = not args.no_persist_artifact

    if args.cycles <= 0:
        parser.error("--cycles must be a positive integer")

    execute_evolution(
        enable_network=args.enable_network,
        persist_artifact=persist_artifact,
        eden88_theme=args.eden88_theme,
        seed=args.seed,
        artifact=args.artifact,
        cycles=args.cycles,
        persist_intermediate=args.persist_intermediate,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
