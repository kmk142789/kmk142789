"""Craft innovation manifests from EchoEvolver runs.

The script orchestrates a short EchoEvolver simulation, feeds every
resulting snapshot into :class:`echo.innovation_forge.InnovationForge`,
and prints either a human-readable innovation chronicle or a JSON
manifest.  It never touches the network and mirrors the deterministic
execution style used throughout the repository.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterable, Optional
import sys

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]
CORE_SRC = REPO_ROOT / "packages" / "core" / "src"

for entry in (REPO_ROOT, CORE_SRC):
    entry_str = entry.as_posix()
    if entry_str not in sys.path:
        sys.path.insert(0, entry_str)

from echo.evolver import EchoEvolver
from echo.innovation_forge import InnovationForge


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Distil EchoEvolver cycles into a unique innovation manifest.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Number of cycles to execute (default: 3).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed for the EchoEvolver RNG to obtain reproducible runs.",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        help="Optional artifact path passed to EchoEvolver.",
    )
    parser.add_argument(
        "--baseline-entropy",
        type=float,
        help="Baseline factor nudging the novelty calculation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the manifest as JSON instead of text.",
    )
    return parser.parse_args(argv)


def _seeded_rng(seed: Optional[int]) -> Optional[random.Random]:
    if seed is None:
        return None
    return random.Random(seed)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    if args.cycles < 1:
        raise SystemExit("--cycles must be at least 1")

    evolver = EchoEvolver(rng=_seeded_rng(args.seed), artifact_path=args.artifact)
    snapshots = evolver.run_cycles(
        args.cycles,
        enable_network=False,
        persist_artifact=False,
        persist_intermediate=False,
    )

    forge = InnovationForge(baseline_entropy=args.baseline_entropy)
    for snapshot in snapshots:
        forge.record_state(snapshot)

    manifest = forge.compose_manifest()

    if args.json:
        print(json.dumps(manifest.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(manifest.render_text())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
