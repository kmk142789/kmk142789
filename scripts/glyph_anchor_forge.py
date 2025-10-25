"""Forge a flood of glyph scripts and anchor them to a JSON feed."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_SRC = PROJECT_ROOT / "packages" / "core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from echo_unified_all import EchoEvolver  # noqa: E402


DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "glyph_anchor_flood.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glyph-anchor-forge",
        description=(
            "Run EchoEvolver cycles that forge Orbital glyph scripts and "
            "emit their data anchors as a JSON feed."
        ),
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of cycles to run (default: 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Optional RNG seed so the forged glyph scripts reproduce across "
            "environments."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination path for the generated JSON payload.",
    )
    return parser


def run_cycles(*, cycles: int, seed: Optional[int]) -> tuple[EchoEvolver, list[dict]]:
    if cycles <= 0:
        raise ValueError("cycles must be a positive integer")

    evolver = EchoEvolver(seed=seed)
    ledger: list[dict] = []

    for _ in range(cycles):
        evolver.run()
        ledger.append(
            {
                "cycle": evolver.state.cycle,
                "glyph_scripts": evolver.state.glyph_scripts,
                "data_anchors": evolver.state.data_anchors,
                "glyphs": evolver.state.glyphs,
                "vault_glyphs": evolver.state.vault_glyphs,
            }
        )

    return evolver, ledger


def write_payload(*, output: Path, ledger: list[dict]) -> None:
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cycles": ledger,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")



def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    evolver, ledger = run_cycles(cycles=args.cycles, seed=args.seed)
    write_payload(output=args.output, ledger=ledger)

    print(
        f"Anchors forged across {len(ledger)} cycle(s); "
        f"payload written to {args.output.resolve()}"
    )
    if evolver.state.glyph_scripts:
        lead = evolver.state.glyph_scripts[0]["name"]
    else:
        lead = "No glyph scripts recorded"
    print(
        "Latest cycle summary: "
        f"{lead} … {len(evolver.state.data_anchors)} anchors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
