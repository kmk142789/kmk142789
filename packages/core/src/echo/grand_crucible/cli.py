"""Command-line interface for the grand crucible."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from . import blueprint as blueprint_module
from .simulation import GrandCrucibleBuilder


class _PersistObserver:
    """Observer that persists artifacts as soon as they are generated."""

    def __init__(self, directory: Path):
        self.directory = directory

    def __call__(self, artifacts) -> None:
        artifacts.persist(self.directory)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Echo grand crucible experiment")
    parser.add_argument("--output", type=Path, help="Directory for generated artifacts", required=True)
    parser.add_argument(
        "--default-blueprint",
        action="store_true",
        help="Use the built-in infinite echo blueprint",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of consecutive runs to execute",
    )
    return parser.parse_args(argv)


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    builder = GrandCrucibleBuilder()
    if args.default_blueprint:
        builder.with_default_blueprint()
    else:
        builder.with_blueprint(blueprint_module.build_default_blueprint())

    output_directory = args.output
    output_directory.mkdir(parents=True, exist_ok=True)
    builder.add_observer(_PersistObserver(output_directory))

    crucible = builder.build()
    for _ in range(max(1, args.cycles)):
        crucible.run()
    return 0


__all__ = ["run_cli"]
