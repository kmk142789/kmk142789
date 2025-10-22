"""Command-line interface for running EchoEvolver cycles.

This helper mirrors the canonical :meth:`echo.evolver.EchoEvolver.run`
routine and exposes the most common toggles as command-line flags.  It
exists so developers (and curious operators) can evolve the system with a
single invocation without needing to remember the Python API surface.  The
CLI intentionally keeps the behaviour deterministic when a ``--seed`` is
provided which makes automated pipelines and tests easier to reproduce.
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
    return parser


def create_evolver(*, seed: Optional[int], artifact: Optional[Path]) -> EchoEvolver:
    """Instantiate :class:`EchoEvolver` with optional overrides."""

    rng = random.Random(seed) if seed is not None else None
    artifact_path = artifact if artifact is None else Path(artifact)
    return EchoEvolver(rng=rng, artifact_path=artifact_path)


def run_cycle(
    *,
    enable_network: bool,
    persist_artifact: bool,
    eden88_theme: Optional[str],
    seed: Optional[int],
    artifact: Optional[Path],
) -> EchoEvolver:
    """Execute a full cycle and return the configured evolver instance."""

    evolver = create_evolver(seed=seed, artifact=artifact)
    evolver.run(
        enable_network=enable_network,
        persist_artifact=persist_artifact,
        eden88_theme=eden88_theme,
    )
    return evolver


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry-point for the evolve-system command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    persist_artifact = not args.no_persist_artifact

    run_cycle(
        enable_network=args.enable_network,
        persist_artifact=persist_artifact,
        eden88_theme=args.eden88_theme,
        seed=args.seed,
        artifact=args.artifact,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
