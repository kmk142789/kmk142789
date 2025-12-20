"""Command line interface for the Resonance Corridor Planner.

Example usage::

    $ python scripts/orbital_corridor_planner.py --input artifacts/cycles.json
    $ python scripts/orbital_corridor_planner.py --run-cycles 4 \
          --output artifacts/resonance_cycles.json --horizon 8
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from echo.orbital_corridor_planner import ResonanceCorridorPlanner
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
    parser.add_argument(
        "--horizon",
        type=int,
        default=6,
        help="Number of cycles to plan ahead.",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="balanced",
        choices=["balanced", "amplify", "stabilize"],
        help="Planning strategy used to shape the corridor.",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="json",
        choices=["json", "markdown"],
        help="Output format for the corridor plan.",
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
    planner = ResonanceCorridorPlanner(
        analyzer, horizon=args.horizon, strategy=args.strategy
    )
    report = planner.plan()
    if args.format == "markdown":
        print(render_markdown(report))
        return
    print(json.dumps(report, indent=2))


def render_markdown(report: dict) -> str:
    corridor = report["corridor"]
    lines = [
        "# Resonance Corridor Plan",
        "",
        f"- Strategy: `{report['strategy']}`",
        f"- Horizon: `{report['horizon']}`",
        f"- Stability: `{report['stability_band']}`",
        f"- Corridor score: `{corridor['corridor_score']}`",
        "",
        "## Guardrails",
        "",
    ]
    for key, value in report["guardrails"].items():
        lines.append(f"- **{key}**: `{value}`")
    lines.extend(["", "## Windows", ""])
    for window in corridor["windows"]:
        lines.append(
            f"- **{window['phase']}** cycles {window['start_cycle']} → {window['end_cycle']}"
        )
        for action in window["focus"]:
            lines.append(f"  - {action}")
    lines.extend(["", "## Steps", ""])
    for step in corridor["steps"]:
        lines.append(
            f"### Cycle {step['cycle']} · {step['phase']} (risk {step['risk_score']})"
        )
        lines.append(f"- Resonance target: `{step['resonance_target']}`")
        lines.append(f"- Stability target: `{step['stability_target']}`")
        lines.append("- Actions:")
        for action in step["actions"]:
            lines.append(f"  - {action}")
        lines.append("- Directives:")
        for directive in step["directives"]:
            lines.append(
                f"  - **{directive['label']}** ({directive['intensity']}): {directive['rationale']}"
            )
        lines.append("- Resource targets:")
        for key, value in step["resource_targets"].items():
            lines.append(f"  - {key}: `{value}`")
        lines.append("- Risk breakdown:")
        for key, value in step["risk_breakdown"].items():
            lines.append(f"  - {key}: `{value}`")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
