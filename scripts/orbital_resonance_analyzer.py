"""Command line interface for the Orbital Resonance Analyzer.

The CLI can load pre-existing EchoEvolver cycle payloads *or* run a fresh
simulation via ``echo_eye_ai.evolver.EchoEvolver``.  After aggregating the
payloads the tool prints a JSON summary containing glyph statistics,
emotional flux, and resonance projections.

Example usage::

    $ python scripts/orbital_resonance_analyzer.py --input cycles.json
    $ python scripts/orbital_resonance_analyzer.py --run-cycles 4 \
          --output artifacts/resonance_cycles.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from echo.orbital_resonance_analyzer import (
    OrbitalResonanceAnalyzer,
    load_payloads_from_artifact,
)
from echo_eye_ai.evolver import EchoEvolver


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a JSON file containing one or more EchoEvolver payloads.",
    )
    parser.add_argument(
        "--run-cycles",
        type=int,
        default=0,
        metavar="N",
        help="Run N fresh cycles with EchoEvolver before analysis.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/orbital_resonance_cycles.json"),
        help="Destination for freshly generated cycle payloads.",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=Path("artifacts/orbital_resonance_cycle.echo"),
        help="Path used by EchoEvolver when persisting individual cycles.",
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=3,
        help="Window length used when smoothing orbital metrics.",
    )
    return parser.parse_args()


def load_payloads(args: argparse.Namespace) -> List[dict]:
    payloads: List[dict] = []

    if args.run_cycles > 0:
        evolver = EchoEvolver(storage_path=args.storage)
        payloads = evolver.run_cycles(args.run_cycles)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payloads, indent=2), encoding="utf-8")

    if not payloads:
        if not args.input:
            raise SystemExit("Either --input or --run-cycles must be provided")
        payloads = [dict(entry) for entry in load_payloads_from_artifact(args.input)]

    return payloads


def main() -> None:
    args = parse_args()
    payloads = load_payloads(args)
    analyzer = OrbitalResonanceAnalyzer.from_payloads(
        payloads, smoothing_window=args.smoothing_window
    )
    report = analyzer.summary()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

