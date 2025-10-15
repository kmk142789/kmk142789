"""Command line interface for Echo toolkit."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List

from .amplify import AmplifyEngine, NUDGE_SUGGESTIONS
from .tools.forecast import ascii_sparkline, blended_forecast, render_table


def _format_log_rows(indices: List[float]) -> List[str]:
    badges = []
    for value in indices:
        if value >= 90:
            badges.append("🚀")
        elif value >= 80:
            badges.append("✨")
        elif value >= 70:
            badges.append("✅")
        else:
            badges.append("⚠️")
    return badges


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo orchestration CLI")
    parser.add_argument("--log-path", default="state/amplify_log.jsonl")
    parser.add_argument("--manifest-path", default="echo_manifest.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    amplify = subparsers.add_parser("amplify", help="Amplification engine commands")
    amp_sub = amplify.add_subparsers(dest="action", required=True)

    amp_sub.add_parser("now", help="Show the latest amplification snapshot")

    log_cmd = amp_sub.add_parser("log", help="Display amplification history table")
    log_cmd.add_argument("--limit", type=int, default=10, help="Number of cycles to display")

    gate_cmd = amp_sub.add_parser("gate", help="Validate the latest index against a minimum")
    gate_cmd.add_argument("--min", type=float, required=True, help="Minimum acceptable index")

    forecast = subparsers.add_parser("forecast", help="Forecast amplification indices")
    forecast.add_argument("--cycles", type=int, default=12, help="History depth to analyse")
    forecast.add_argument("--plot", action="store_true", help="Render ASCII sparkline plot")

    return parser


def _print_snapshot(engine: AmplifyEngine) -> int:
    snapshot = engine.latest_snapshot()
    if snapshot is None:
        print("No amplification snapshots recorded yet.")
        return 1
    engine.sync_manifest()
    print(
        f"Amplify Index {snapshot.index:.2f} | cycle {snapshot.cycle} | "
        f"timestamp {snapshot.timestamp}"
    )
    for metric in sorted(snapshot.metrics):
        print(f"- {metric}: {snapshot.metrics[metric]:.2f}")
    print(snapshot.to_json())
    return 0


def _print_log(engine: AmplifyEngine, *, limit: int) -> int:
    history = engine.snapshots
    if not history:
        print("No amplification history available.")
        return 0

    start = max(0, len(history) - max(1, limit))
    rows = ["Cycle", "Index", "Δ", "Badge"]
    values = [snap.index for snap in history[start:]]
    badges = _format_log_rows(values)
    table: List[List[str]] = [rows, ["-", "-", "-", "-"]]

    for offset, snapshot in enumerate(history[start:], start=start):
        prev_index = history[offset - 1].index if offset > 0 else None
        delta = 0.0 if prev_index is None else snapshot.index - prev_index
        table.append(
            [
                str(snapshot.cycle),
                f"{snapshot.index:.2f}",
                f"{delta:+.2f}" if prev_index is not None else "N/A",
                badges[offset - start],
            ]
        )

    widths = [max(len(row[idx]) for row in table) for idx in range(len(rows))]
    for row in table:
        print(" ".join(value.rjust(width) for value, width in zip(row, widths)))

    return 0


def _run_gate(engine: AmplifyEngine, *, minimum: float) -> int:
    snapshot = engine.latest_snapshot()
    if snapshot is None:
        print("Amplify gate check failed: no snapshots recorded.")
        return 2
    if snapshot.index >= minimum:
        print(
            f"Gate satisfied: latest index {snapshot.index:.2f} meets minimum {minimum:.2f}."
        )
        return 0

    print(
        f"Amplify gate {minimum:.2f} not met: latest index {snapshot.index:.2f}."
    )
    dips = [
        NUDGE_SUGGESTIONS.get(metric)
        for metric, value in snapshot.metrics.items()
        if value < engine.thresholds.get(metric, 0.0)
    ]
    suggestions = [message for message in dips if message]
    if not suggestions:
        suggestions = [
            "Re-run echo amplify log for context and initiate continue_cycle() with refactors.",
        ]
    print("Suggested actions:")
    for message in suggestions:
        print(f"- {message}")
    return 2


def _run_forecast(engine: AmplifyEngine, *, cycles: int, plot: bool) -> int:
    history = [snapshot.index for snapshot in engine.snapshots]
    if not history:
        print("No amplification history available to forecast.")
        return 1

    subset = history[-max(1, cycles) :]
    result = blended_forecast(subset)
    print(f"Analysed {len(subset)} cycles | volatility ±{result.volatility:.2f}")
    print(render_table(result))
    if plot:
        combined = subset + [point.value for point in result.projections]
        print(f"Sparkline: {ascii_sparkline(combined)}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    engine = AmplifyEngine(log_path=args.log_path, manifest_path=args.manifest_path)

    if args.command == "amplify":
        if args.action == "now":
            return _print_snapshot(engine)
        if args.action == "log":
            return _print_log(engine, limit=args.limit)
        if args.action == "gate":
            return _run_gate(engine, minimum=args.min)
    elif args.command == "forecast":
        return _run_forecast(engine, cycles=args.cycles, plot=args.plot)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())

