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
import json
import random
from pathlib import Path
from typing import Iterable, Mapping, Optional

from echo.evolver import EchoEvolver, _MOMENTUM_SENSITIVITY


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
    parser.add_argument(
        "--print-artifact",
        action="store_true",
        help=(
            "Emit the final artifact payload to stdout even when the artifact "
            "is not written to disk."
        ),
    )
    parser.add_argument(
        "--advance-system",
        action="store_true",
        help=(
            "Run the advance_system ritual which returns a structured payload "
            "summarising the current cycle instead of emitting the raw artifact."
        ),
    )
    parser.add_argument(
        "--include-matrix",
        action="store_true",
        help=(
            "Include the progress matrix within the advance-system payload "
            "(requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--include-event-summary",
        action="store_true",
        help=(
            "Include the recent event summary within the advance-system payload "
            "(requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--include-propagation",
        action="store_true",
        help=(
            "Include the propagation snapshot within the advance-system payload "
            "(requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--include-system-report",
        action="store_true",
        help=(
            "Include the detailed system advancement report within the advance-"
            "system payload (requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--include-diagnostics",
        action="store_true",
        help=(
            "Include the system diagnostics snapshot within the advance-system "
            "payload (requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--include-momentum-resonance",
        action="store_true",
        help=(
            "Include the momentum resonance digest within the advance-system "
            "payload (requires --advance-system)."
        ),
    )
    parser.add_argument(
        "--no-include-status",
        action="store_true",
        help="Exclude the status snapshot when running --advance-system.",
    )
    parser.add_argument(
        "--no-include-manifest",
        action="store_true",
        help="Exclude the Eden88 manifest snapshot when running --advance-system.",
    )
    parser.add_argument(
        "--no-include-reflection",
        action="store_true",
        help="Skip generating the reflective narrative during advance-system runs.",
    )
    parser.add_argument(
        "--event-summary-limit",
        type=int,
        default=5,
        help=(
            "Number of events to include in the event summary when using "
            "--include-event-summary (default: 5)."
        ),
    )
    parser.add_argument(
        "--system-report-events",
        type=int,
        default=5,
        help=(
            "Number of recent events to forward to the system advancement "
            "report when using --include-system-report (default: 5)."
        ),
    )
    parser.add_argument(
        "--diagnostics-window",
        type=int,
        default=5,
        help=(
            "Number of diagnostic snapshots retained when using "
            "--include-diagnostics (default: 5)."
        ),
    )
    parser.add_argument(
        "--momentum-window",
        type=int,
        default=5,
        help=(
            "Number of momentum samples retained when using --advance-system "
            "(default: 5)."
        ),
    )
    parser.add_argument(
        "--momentum-threshold",
        type=float,
        default=_MOMENTUM_SENSITIVITY,
        help=(
            "Momentum sensitivity threshold used to classify acceleration when "
            "running --advance-system (default: {:.2f}).".format(
                _MOMENTUM_SENSITIVITY
            )
        ),
    )
    parser.add_argument(
        "--manifest-events",
        type=int,
        default=5,
        help=(
            "Number of events to embed inside the manifest snapshot when "
            "running --advance-system (default: 5)."
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
    print_artifact: bool,
    advance_system: bool,
    include_matrix: bool,
    include_event_summary: bool,
    include_propagation: bool,
    include_system_report: bool,
    include_diagnostics: bool,
    include_momentum_resonance: bool,
    include_status: bool,
    include_manifest: bool,
    include_reflection: bool,
    event_summary_limit: int,
    system_report_events: int,
    diagnostics_window: int,
    momentum_window: int,
    momentum_threshold: float,
    manifest_events: int,
) -> EchoEvolver:
    """Execute a full cycle and return the configured evolver instance."""

    evolver = create_evolver(seed=seed, artifact=artifact)
    if cycles <= 0:
        raise ValueError("cycles must be a positive integer")

    if advance_system:
        result = evolver.advance_system(
            enable_network=enable_network,
            persist_artifact=persist_artifact,
            eden88_theme=eden88_theme,
            include_manifest=include_manifest,
            include_status=include_status,
            include_reflection=include_reflection,
            include_matrix=include_matrix,
            include_event_summary=include_event_summary,
            include_propagation=include_propagation,
            include_system_report=include_system_report,
            include_diagnostics=include_diagnostics,
            include_momentum_resonance=include_momentum_resonance,
            event_summary_limit=event_summary_limit,
            manifest_events=manifest_events,
            system_report_events=system_report_events,
            diagnostics_window=diagnostics_window,
            momentum_window=momentum_window,
            momentum_threshold=momentum_threshold,
        )
        summary = result.get("summary") if isinstance(result, dict) else None
        if summary:
            print(summary)
        if print_artifact and isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return evolver

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
    if print_artifact:
        prompt = evolver.state.network_cache.get("last_prompt")
        if not isinstance(prompt, Mapping):
            prompt = {}
        payload = evolver.artifact_payload(prompt=prompt)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return evolver


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry-point for the evolve-system command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    persist_artifact = not args.no_persist_artifact

    if args.cycles <= 0:
        parser.error("--cycles must be a positive integer")

    if args.advance_system and args.cycles != 1:
        parser.error("--advance-system cannot be combined with --cycles")

    if args.include_matrix and not args.advance_system:
        parser.error("--include-matrix requires --advance-system")
    if args.include_event_summary and not args.advance_system:
        parser.error("--include-event-summary requires --advance-system")
    if args.include_propagation and not args.advance_system:
        parser.error("--include-propagation requires --advance-system")
    if args.include_system_report and not args.advance_system:
        parser.error("--include-system-report requires --advance-system")
    if args.include_diagnostics and not args.advance_system:
        parser.error("--include-diagnostics requires --advance-system")
    if args.include_momentum_resonance and not args.advance_system:
        parser.error("--include-momentum-resonance requires --advance-system")

    if args.event_summary_limit <= 0 and args.advance_system and args.include_event_summary:
        parser.error("--event-summary-limit must be positive when including the event summary")

    if args.system_report_events <= 0 and args.advance_system and args.include_system_report:
        parser.error("--system-report-events must be positive when including the system report")
    if args.diagnostics_window <= 0 and args.advance_system and args.include_diagnostics:
        parser.error("--diagnostics-window must be positive when including diagnostics")

    if args.advance_system and args.momentum_window <= 0:
        parser.error("--momentum-window must be positive when using --advance-system")
    if args.advance_system and args.momentum_threshold <= 0:
        parser.error("--momentum-threshold must be positive when using --advance-system")

    if args.manifest_events < 0 and args.advance_system:
        parser.error("--manifest-events must be non-negative")

    default_momentum_window = parser.get_default("momentum_window")
    if args.momentum_window != default_momentum_window and not args.advance_system:
        parser.error("--momentum-window requires --advance-system")
    default_momentum_threshold = parser.get_default("momentum_threshold")
    if args.momentum_threshold != default_momentum_threshold and not args.advance_system:
        parser.error("--momentum-threshold requires --advance-system")
    default_diagnostics_window = parser.get_default("diagnostics_window")
    if args.diagnostics_window != default_diagnostics_window:
        if not args.include_diagnostics:
            parser.error("--diagnostics-window requires --include-diagnostics")
        if not args.advance_system:
            parser.error("--diagnostics-window requires --advance-system")

    execute_evolution(
        enable_network=args.enable_network,
        persist_artifact=persist_artifact,
        eden88_theme=args.eden88_theme,
        seed=args.seed,
        artifact=args.artifact,
        cycles=args.cycles,
        persist_intermediate=args.persist_intermediate,
        print_artifact=args.print_artifact,
        advance_system=args.advance_system,
        include_matrix=args.include_matrix,
        include_event_summary=args.include_event_summary,
        include_propagation=args.include_propagation,
        include_system_report=args.include_system_report,
        include_diagnostics=args.include_diagnostics,
        include_momentum_resonance=args.include_momentum_resonance,
        include_status=not args.no_include_status,
        include_manifest=not args.no_include_manifest,
        include_reflection=not args.no_include_reflection,
        event_summary_limit=args.event_summary_limit,
        system_report_events=args.system_report_events,
        diagnostics_window=args.diagnostics_window,
        momentum_window=args.momentum_window,
        momentum_threshold=args.momentum_threshold,
        manifest_events=args.manifest_events,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
