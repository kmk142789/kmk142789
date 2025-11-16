"""Command line interface for the Hyperdimensional Resonance Engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover - import shim for script execution
    from .hyperdimensional_resonance_engine import HyperdimensionalResonanceEngine
except ImportError:  # pragma: no cover
    from hyperdimensional_resonance_engine import HyperdimensionalResonanceEngine


def _default_blueprint() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "config" / "hyperdimensional_resonance.json"


def run_cli(argv: Any = None) -> None:
    parser = argparse.ArgumentParser(description="Hyperdimensional Resonance Engine")
    parser.add_argument(
        "--blueprint",
        type=Path,
        default=_default_blueprint(),
        help="Path to the blueprint JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file to store the summarized report",
    )
    args = parser.parse_args(argv)

    engine, pulses = HyperdimensionalResonanceEngine.from_blueprint(args.blueprint)
    report = engine.run(pulses)

    summary = {
        "cycles": report.cycle_count,
        "pulse_count": len(report.pulses),
        "duration": report.duration,
        "metrics": report.metrics,
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2))
    else:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_cli()

