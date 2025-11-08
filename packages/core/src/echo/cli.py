"""Legacy compatibility CLI for the Echo project.

The primary command entry point for the ``echo`` console script now lives in
``echo.manifest_cli``.  This shim keeps the old module importable while
delegating to the new implementation.  It exposes a reduced set of commands
that mirror the previous behaviour but rely on the modern manifest helpers.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, NoReturn

from pulse_weaver.cli import register_subcommand as register_pulse_weaver

from .amplify import AmplificationEngine, AmplifyState
from .evolver import EchoEvolver
from .manifest_cli import refresh_manifest, show_manifest, verify_manifest
from .timeline import build_cycle_timeline, refresh_cycle_timeline
from .tools.forecast import project_indices, sparkline
from .novelty import NoveltyGenerator
from .self_sustaining_loop import SelfSustainingLoop
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import PulseBus, WatchdogConfig, build_pulse_bus, build_watchdog


EXPECTED_STEPS = 13

AGGREGATE_SEGMENTS = {
    "category": 0,
    "source": 1,
    "detail": 2,
}


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _cmd_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def _cmd_evolve(args: argparse.Namespace) -> int:
    parser: argparse.ArgumentParser | None = getattr(args, "_parser", None)

    def parser_error(message: str) -> NoReturn:  # pragma: no cover - exercised via argparse
        if parser is not None:
            parser.error(message)
        raise SystemExit(2)

    rng = random.Random(args.seed) if args.seed is not None else None
    artifact_path = args.artifact
    persist_artifact = not args.no_persist_artifact

    if args.advance_system and args.cycles != 1:
        parser_error("--advance-system can only be used with a single cycle")
    if args.advance_system and args.describe_sequence:
        parser_error("--advance-system cannot be combined with --describe-sequence")
    if args.advance_system and args.persist_intermediate:
        parser_error("--advance-system cannot be combined with --persist-intermediate")

    if args.include_event_summary and args.event_summary_limit <= 0:
        parser_error("--event-summary-limit must be positive when including the event summary")
    if args.include_system_report and args.system_report_events <= 0:
        parser_error("--system-report-events must be positive when including the system report")
    if args.manifest_events < 0:
        parser_error("--manifest-events must be non-negative")

    if not args.advance_system:
        default_summary_limit = parser.get_default("event_summary_limit") if parser else 5
        if args.event_summary_limit != default_summary_limit:
            parser_error("--event-summary-limit requires --advance-system")

        default_system_events = parser.get_default("system_report_events") if parser else 5
        if args.system_report_events != default_system_events:
            parser_error("--system-report-events requires --advance-system")

        default_manifest_events = parser.get_default("manifest_events") if parser else 5
        if args.manifest_events != default_manifest_events:
            parser_error("--manifest-events requires --advance-system")

    if args.event_summary_limit > 0 and not args.include_event_summary:
        default_summary_limit = parser.get_default("event_summary_limit") if parser else 5
        if args.event_summary_limit != default_summary_limit:
            parser_error("--event-summary-limit requires --include-event-summary")

    if args.system_report_events > 0 and not args.include_system_report:
        default_system_events = parser.get_default("system_report_events") if parser else 5
        if args.system_report_events != default_system_events:
            parser_error("--system-report-events requires --include-system-report")

    if args.manifest_events >= 0 and not args.include_manifest:
        default_manifest_events = parser.get_default("manifest_events") if parser else 5
        if args.manifest_events != default_manifest_events:
            parser_error("--manifest-events requires --include-manifest")

    if (
        not args.advance_system
        and (
            args.include_matrix
            or args.include_event_summary
            or args.include_propagation
            or args.include_system_report
        )
    ):
        parser_error(
            "--include-matrix, --include-event-summary, --include-propagation, and --include-system-report require --advance-system"
        )

    evolver = EchoEvolver(rng=rng, artifact_path=artifact_path)

    if args.describe_sequence:
        print(evolver.describe_sequence(persist_artifact=persist_artifact))
        return 0

    if args.advance_system:
        payload = evolver.advance_system(
            enable_network=args.enable_network,
            persist_artifact=persist_artifact,
            eden88_theme=args.eden88_theme,
            include_manifest=args.include_manifest,
            include_status=args.include_status,
            include_reflection=args.include_reflection,
            include_matrix=args.include_matrix,
            include_event_summary=args.include_event_summary,
            include_propagation=args.include_propagation,
            include_system_report=args.include_system_report,
            event_summary_limit=args.event_summary_limit,
            manifest_events=args.manifest_events,
            system_report_events=args.system_report_events,
        )
        summary = payload.get("summary") if isinstance(payload, Mapping) else None
        if summary:
            print(summary)
        if args.print_artifact and isinstance(payload, Mapping):
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.cycles == 1:
        evolver.run(
            enable_network=args.enable_network,
            persist_artifact=persist_artifact,
            eden88_theme=args.eden88_theme,
        )
    else:
        evolver.run_cycles(
            args.cycles,
            enable_network=args.enable_network,
            persist_artifact=persist_artifact,
            persist_intermediate=args.persist_intermediate,
            eden88_theme=args.eden88_theme,
        )

    if args.print_artifact:
        prompt = evolver.state.network_cache.get("last_prompt")
        if not isinstance(prompt, Mapping):
            prompt = {}
        payload = evolver.artifact_payload(prompt=prompt)
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0


def _cmd_novelty(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed) if args.seed is not None else None
    generator = NoveltyGenerator(rng=rng)
    sparks = generator.generate(count=args.count, theme=args.theme)

    for index, spark in enumerate(sparks, start=1):
        if args.count > 1:
            print(f"# Spark {index}")
        print(spark.render())
        if index != len(sparks):
            print()
    return 0


def _load_state_from_manifest(path: Path | None) -> AmplifyState:
    manifest_path = path or Path("echo_manifest.json")
    if not manifest_path.exists():
        return AmplifyState(
            cycle=0,
            joy=0.9,
            curiosity=0.9,
            rage=0.2,
            completed_steps=EXPECTED_STEPS,
            expected_steps=EXPECTED_STEPS,
            mythocode_count=0,
            propagation_channels=0,
            events=0,
            network_nodes=0,
            orbital_hops=0,
        )

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    evolver = data.get("evolver", {})
    emotional = evolver.get("emotional_drive", {})
    events: List[str] = data.get("events", []) or []
    mythocode: List[str] = data.get("mythocode", []) or []
    return AmplifyState(
        cycle=int(evolver.get("cycle", 0)),
        joy=float(emotional.get("joy", 0.9)),
        curiosity=float(emotional.get("curiosity", 0.9)),
        rage=float(emotional.get("rage", 0.2)),
        completed_steps=EXPECTED_STEPS,
        expected_steps=EXPECTED_STEPS,
        mythocode_count=len(mythocode),
        propagation_channels=int(evolver.get("propagation_channels", 0)),
        events=len(events),
        network_nodes=int(evolver.get("network_nodes", 0)),
        orbital_hops=int(evolver.get("orbital_hops", 0)),
    )


def _cmd_amplify_now(args: argparse.Namespace) -> int:
    engine = AmplificationEngine(
        log_path=args.log_path,
        manifest_path=args.manifest,
    )
    history = engine.load_history()
    state = _load_state_from_manifest(args.manifest)
    snapshot = engine.build_snapshot(
        state,
        previous=history[-1] if history else None,
    )
    engine.persist_snapshot(snapshot)
    engine.update_manifest(snapshot)

    print(
        f"Amplify Snapshot :: cycle {snapshot.cycle} | index {snapshot.index:.2f} | commit {snapshot.commit_sha}"
    )
    for name, value in snapshot.metrics.as_dict().items():
        print(f"  - {name}: {value}")
    print()
    print(json.dumps(snapshot.as_dict(), sort_keys=True, indent=2))
    return 0


def _cmd_amplify_log(args: argparse.Namespace) -> int:
    engine = AmplificationEngine(log_path=args.log_path, manifest_path=args.manifest)
    history = engine.load_history()
    if not history:
        print("No amplification history available.")
        return 0

    limit = args.limit
    print("Cycle | Index | Δ | Timestamp")
    print("------|-------|----|------------------------")
    last_index = None
    for snapshot in history[-limit:]:
        delta = "∅" if last_index is None else f"{snapshot.index - last_index:+.2f}"
        print(
            f"{snapshot.cycle:5d} | {snapshot.index:5.1f} | {delta:>4} | {snapshot.timestamp}"
        )
        last_index = snapshot.index
    return 0


def _cmd_amplify_gate(args: argparse.Namespace) -> int:
    engine = AmplificationEngine(log_path=args.log_path, manifest_path=args.manifest)
    try:
        engine.require_gate(minimum=args.minimum)
    except Exception as exc:  # pragma: no cover - defensive
        print(str(exc))
        return 1
    print(
        f"Amplify gate passed: rolling average >= {args.minimum}"
    )
    return 0


def _cmd_forecast(args: argparse.Namespace) -> int:
    engine = AmplificationEngine(log_path=args.log_path, manifest_path=args.manifest)
    history = engine.load_history()
    if not history:
        print("No amplification data available for forecasting.")
        return 1

    indices = [snapshot.index for snapshot in history[-args.cycles :]]
    result = project_indices(indices, horizon=3)
    print("Baseline | +1 | +2 | +3 | ±band")
    print("---------|----|----|----|-------")
    print(
        f"{result.baseline:7.2f} | {result.projections[0]:4.2f} | {result.projections[1]:4.2f} | "
        f"{result.projections[2]:4.2f} | ±{result.confidence_band:4.2f}"
    )
    if args.plot:
        series = indices + result.projections
        line = sparkline(series)
        print()
        print(f"sparkline: {line}")
    return 0


def _load_signing_key(path: Path) -> Mapping[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "private_key" not in data or "key_id" not in data:
        raise ValueError("key file must contain 'private_key' and 'key_id'")
    return {"private_key": str(data["private_key"]), "key_id": str(data["key_id"]), "public_key": data.get("public_key")}


def _cmd_pulse_watch(args: argparse.Namespace) -> int:
    watchdog = build_watchdog()
    failures = watchdog.detect_failures()
    if not failures:
        print("No failure events detected.")
        return 0
    event = failures[-1]
    reason = args.reason or str(event.get("reason", "auto"))
    config = WatchdogConfig(
        dry_run_only=args.dry_run,
        max_attempts=args.max_attempts,
        cooldown_seconds=args.cooldown_sec,
    )
    report = watchdog.run_cycle(event, reason=reason, config=config)
    print(f"Watchdog run for {reason}: {'success' if report.succeeded else 'failure'}")
    if report.proof_path:
        print(f"Proof: {report.proof_path}")
    return 0 if report.succeeded else 1


def _cmd_pulse_emit(args: argparse.Namespace) -> int:
    state_dir = args.state or Path("state")
    signing_key: Mapping[str, str] | None = None
    if args.key_file:
        signing_key = _load_signing_key(args.key_file)
    elif args.private_key and args.key_id:
        signing_key = {"private_key": args.private_key, "key_id": args.key_id}
    bus = build_pulse_bus(state_dir)
    if signing_key:
        bus = PulseBus(
            state_dir=state_dir,
            signing_key=signing_key,
            known_keys_path=state_dir / "pulses/keys.json",
        )
        if args.public_key and "public_key" in signing_key:
            bus.register_key(signing_key["key_id"], signing_key["public_key"])
    outbox_entry = bus.emit(
        args.repo,
        args.ref,
        kind=args.kind,
        summary=args.summary,
        proof_id=args.proof,
        destinations=args.dest or [],
    )
    print(json.dumps(outbox_entry.envelope.model_dump(), indent=2, sort_keys=True))
    print(f"Saved to {outbox_entry.path}")
    return 0


def _normalise_pulse_message(message: str) -> str:
    text = message or ""
    while text and not text[0].isalnum():
        text = text[1:]
    return text.strip()


def _extract_segment(message: str, segment: str) -> str:
    index = AGGREGATE_SEGMENTS[segment]
    parts = _normalise_pulse_message(message).split(":")
    if index < len(parts) and parts[index]:
        return parts[index]
    return "<unknown>"


def _cmd_pulse_history(args: argparse.Namespace) -> int:
    history_path = args.path or Path("pulse_history.json")
    if not history_path.exists():
        print(f"No pulse history found at {history_path}")
        return 1

    try:
        entries = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        print(f"Failed to parse pulse history: {exc}")
        return 1

    since_ts: float | None = None
    if args.since:
        dt = datetime.fromisoformat(args.since)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        since_ts = dt.timestamp()

    if since_ts is not None:
        entries = [entry for entry in entries if entry.get("timestamp", 0) >= since_ts]

    if args.limit is not None:
        entries = entries[-args.limit :]

    if not entries:
        print("No pulse events available for the selected range.")
        return 0

    if args.aggregate:
        counts: dict[str, int] = {}
        for entry in entries:
            key = _extract_segment(entry.get("message", ""), args.aggregate)
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            print("No events available to aggregate.")
            return 0

        header = args.aggregate.capitalize()
        width = max(len(header), max((len(key) for key in counts), default=0))
        print(f"{header:<{width}} | Count")
        print(f"{'-' * width}-|-------")
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"{key:<{width}} | {count:5d}")
        return 0

    print("Timestamp (UTC)        | Message")
    print("-----------------------|--------------------------------")
    for entry in entries:
        ts = datetime.fromtimestamp(entry.get("timestamp", 0), tz=timezone.utc)
        message = entry.get("message", "")
        print(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} | {message}")
    return 0


def _cmd_timeline(args: argparse.Namespace) -> int:
    project_root = args.project_root or Path.cwd()
    if args.cycle is not None:
        entries = build_cycle_timeline(
            project_root=project_root,
            amplify_log=args.amplify_log,
            pulse_history=args.pulse_history,
            puzzle_index=args.puzzle_index,
            limit=args.limit,
        )
        if not entries:
            print("No cycle snapshots available.")
            return 1
        for entry in entries:
            if entry.snapshot.cycle == args.cycle:
                print(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
                print()
                print(entry.to_markdown())
                return 0
        print(f"No timeline entry for cycle {args.cycle}.")
        return 1

    entries = refresh_cycle_timeline(
        project_root=project_root,
        amplify_log=args.amplify_log,
        pulse_history=args.pulse_history,
        puzzle_index=args.puzzle_index,
        output_dir=args.out,
        limit=args.limit,
    )
    if not entries:
        print("No cycle snapshots available; timeline exports not created.")
        return 1

    if args.out is not None:
        target_dir = Path(args.out)
        if not target_dir.is_absolute():
            target_dir = project_root / target_dir
    else:
        target_dir = project_root / "artifacts"
    print(f"Cycle timeline exports refreshed in {target_dir}")
    return 0


def _cmd_ledger_snapshot(args: argparse.Namespace) -> int:
    ledger = TemporalLedger(state_dir=args.state or Path("state"))
    since = datetime.fromisoformat(args.since) if args.since else None
    limit = args.limit
    if args.format == "md":
        content = ledger.as_markdown(since=since, limit=limit)
        suffix = ".md"
    elif args.format == "svg":
        content = ledger.as_svg(since=since, limit=limit)
        suffix = ".svg"
    else:  # pragma: no cover - defensive branch
        raise ValueError("Unsupported format")
    output_dir = args.out or Path("artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"ledger_snapshot{suffix}"
    path.write_text(content, encoding="utf-8")
    print(f"Snapshot written to {path}")
    return 0


def _cmd_ledger_tail(args: argparse.Namespace) -> int:
    ledger = TemporalLedger(state_dir=args.state or Path("state"))
    since = datetime.fromisoformat(args.since) if args.since else None
    entries = list(ledger.iter_entries(since=since, limit=args.limit))
    if not entries:
        print("No ledger entries available.")
        return 0
    for entry in entries:
        print(f"{entry.ts.isoformat()} | {entry.actor} | {entry.action} | {entry.ref} | {entry.hash[:8]}")
    return 0


def _load_loop_state(loop: SelfSustainingLoop) -> Mapping[str, object]:
    return json.loads(loop.state_path.read_text(encoding="utf-8"))


def _cmd_loop_cycle(args: argparse.Namespace) -> int:
    loop = SelfSustainingLoop(args.root)
    try:
        loop.progress(args.summary, actor=args.actor)
    except ValueError as exc:  # pragma: no cover - validation surfaced to callers
        print(str(exc))
        return 1
    state = _load_loop_state(loop)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def _cmd_loop_status(args: argparse.Namespace) -> int:
    loop = SelfSustainingLoop(args.root)
    state = _load_loop_state(loop)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def _cmd_loop_govern(args: argparse.Namespace) -> int:
    loop = SelfSustainingLoop(args.root)
    decision = (
        "approve"
        if args.approve
        else "reject"
        if args.reject
        else "auto-merge"
    )
    result = loop.decide(args.proposal_id, decision, actor=args.actor, reason=args.reason)
    payload = json.loads(result.path.read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_loop_export(args: argparse.Namespace) -> int:
    loop = SelfSustainingLoop(args.root)
    state = _load_loop_state(loop)
    proposals = loop.list_proposals()
    payload = {"state": state, "proposals": proposals}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="echo",
        description="Echo compatibility CLI (delegates to echo.manifest_cli)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_pulse_weaver(subparsers)

    refresh_parser = subparsers.add_parser("manifest-refresh", help="Refresh manifest")
    refresh_parser.add_argument("--path", type=Path, help="Optional manifest path")
    refresh_parser.set_defaults(func=_cmd_refresh)

    show_parser = subparsers.add_parser("manifest-show", help="Show manifest summary")
    show_parser.add_argument("--path", type=Path, help="Optional manifest path")
    show_parser.set_defaults(func=_cmd_show)

    verify_parser = subparsers.add_parser("manifest-verify", help="Verify manifest digest")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=_cmd_verify)

    evolve_parser = subparsers.add_parser("evolve", help="Run EchoEvolver cycles")
    evolve_parser.add_argument(
        "--enable-network",
        action="store_true",
        help=(
            "Include propagation events that describe live network intent. "
            "All actions remain simulated for safety."
        ),
    )
    evolve_parser.add_argument(
        "--no-persist-artifact",
        action="store_true",
        help="Skip writing the cycle artifact to disk.",
    )
    evolve_parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help="Optional path for the persisted artifact.",
    )
    evolve_parser.add_argument(
        "--eden88-theme",
        default=None,
        help="Override the theme used when crafting the sanctuary artifact.",
    )
    evolve_parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed value for the evolver RNG.",
    )
    evolve_parser.add_argument(
        "--cycles",
        type=_positive_int,
        default=1,
        help="Number of sequential cycles to run (default: 1).",
    )
    evolve_parser.add_argument(
        "--persist-intermediate",
        action="store_true",
        help="Persist artifacts after every cycle when running multiple cycles.",
    )
    evolve_parser.add_argument(
        "--print-artifact",
        action="store_true",
        help="Emit the final artifact payload to stdout.",
    )
    evolve_parser.add_argument(
        "--describe-sequence",
        action="store_true",
        help=(
            "Render the recommended ritual sequence and exit without running a cycle."
        ),
    )
    evolve_parser.add_argument(
        "--advance-system",
        action="store_true",
        help=(
            "Run the advance_system ritual and emit a structured payload "
            "describing the current cycle."
        ),
    )
    evolve_parser.add_argument(
        "--include-matrix",
        action="store_true",
        help=(
            "Include the progress matrix snapshot when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-event-summary",
        action="store_true",
        help=(
            "Include the recent event summary when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-propagation",
        action="store_true",
        help=(
            "Include the propagation snapshot when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-system-report",
        action="store_true",
        help=(
            "Include the detailed system advancement report when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--event-summary-limit",
        type=int,
        default=5,
        help=(
            "Number of events to include in the summary when using --include-event-summary "
            "(default: 5)."
        ),
    )
    evolve_parser.add_argument(
        "--system-report-events",
        type=int,
        default=5,
        help=(
            "Number of events to include in the system report when using --include-system-report "
            "(default: 5)."
        ),
    )
    evolve_parser.add_argument(
        "--manifest-events",
        type=int,
        default=5,
        help=(
            "Number of events to embed within the Eden88 manifest when using --advance-system "
            "(default: 5)."
        ),
    )
    evolve_parser.add_argument(
        "--no-include-status",
        dest="include_status",
        action="store_false",
        help="Exclude the evolution status snapshot when using --advance-system.",
    )
    evolve_parser.add_argument(
        "--no-include-manifest",
        dest="include_manifest",
        action="store_false",
        help="Exclude the Eden88 manifest snapshot when using --advance-system.",
    )
    evolve_parser.add_argument(
        "--no-include-reflection",
        dest="include_reflection",
        action="store_false",
        help="Skip the reflective narrative when using --advance-system.",
    )
    evolve_parser.set_defaults(
        func=_cmd_evolve,
        include_status=True,
        include_manifest=True,
        include_reflection=True,
        _parser=evolve_parser,
    )

    novelty_parser = subparsers.add_parser(
        "novelty", help="Generate a burst of fresh Echo sparks"
    )
    novelty_parser.add_argument(
        "--count",
        type=_positive_int,
        default=1,
        help="Number of sparks to generate (default: 1)",
    )
    novelty_parser.add_argument(
        "--theme",
        help="Optional theme to weave into each spark",
    )
    novelty_parser.add_argument(
        "--seed",
        type=int,
        help="Seed for deterministic spark generation",
    )
    novelty_parser.set_defaults(func=_cmd_novelty)

    amplify_parser = subparsers.add_parser("amplify", help="Amplification engine commands")
    amplify_sub = amplify_parser.add_subparsers(dest="amp_command", required=True)

    now_parser = amplify_sub.add_parser("now", help="Compute current amplification snapshot")
    now_parser.add_argument("--manifest", type=Path, default=Path("echo_manifest.json"))
    now_parser.add_argument(
        "--log-path",
        dest="log_path",
        type=Path,
        default=Path("state/amplify_log.jsonl"),
    )
    now_parser.set_defaults(func=_cmd_amplify_now)

    log_parser = amplify_sub.add_parser("log", help="Show recent amplification history")
    log_parser.add_argument("--manifest", type=Path, default=Path("echo_manifest.json"))
    log_parser.add_argument(
        "--log-path",
        dest="log_path",
        type=Path,
        default=Path("state/amplify_log.jsonl"),
    )
    log_parser.add_argument("--limit", type=int, default=5)
    log_parser.set_defaults(func=_cmd_amplify_log)

    gate_parser = amplify_sub.add_parser("gate", help="Enforce amplification threshold")
    gate_parser.add_argument("--manifest", type=Path, default=Path("echo_manifest.json"))
    gate_parser.add_argument(
        "--log-path",
        dest="log_path",
        type=Path,
        default=Path("state/amplify_log.jsonl"),
    )
    gate_parser.add_argument("--min", dest="minimum", type=float, required=True)
    gate_parser.set_defaults(func=_cmd_amplify_gate)

    forecast_parser = subparsers.add_parser("forecast", help="Project amplification indices")
    forecast_parser.add_argument("--manifest", type=Path, default=Path("echo_manifest.json"))
    forecast_parser.add_argument(
        "--log-path",
        dest="log_path",
        type=Path,
        default=Path("state/amplify_log.jsonl"),
    )
    forecast_parser.add_argument("--cycles", type=int, default=12)
    forecast_parser.add_argument("--plot", action="store_true")
    forecast_parser.set_defaults(func=_cmd_forecast)

    loop_parser = subparsers.add_parser(
        "unified-sentience-loop",
        help="Manage the self-sustaining planning orchestrator",
    )
    loop_parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory used to resolve orchestrator state (default: current directory)",
    )
    loop_sub = loop_parser.add_subparsers(dest="loop_command", required=True)

    loop_cycle = loop_sub.add_parser("cycle", help="Record progress for the active cycle")
    loop_cycle.add_argument("--summary", required=True, help="Description of the completed work")
    loop_cycle.add_argument(
        "--actor",
        default="automation",
        help="Actor recording the progress entry",
    )
    loop_cycle.set_defaults(func=_cmd_loop_cycle)

    loop_status = loop_sub.add_parser("status", help="Display the orchestrator state")
    loop_status.set_defaults(func=_cmd_loop_status)

    loop_govern = loop_sub.add_parser("govern", help="Record a governance decision")
    loop_govern.add_argument("proposal_id", help="Proposal identifier (cycle_XXXX)")
    decision_opts = loop_govern.add_mutually_exclusive_group(required=True)
    decision_opts.add_argument("--approve", action="store_true", help="Approve the proposal")
    decision_opts.add_argument("--reject", action="store_true", help="Reject the proposal")
    decision_opts.add_argument(
        "--auto-merge",
        dest="auto_merge",
        action="store_true",
        help="Mark the proposal for auto-merge",
    )
    loop_govern.add_argument("--actor", default="governance", help="Decision maker")
    loop_govern.add_argument("--reason", default=None, help="Decision rationale")
    loop_govern.set_defaults(func=_cmd_loop_govern)

    loop_export = loop_sub.add_parser("export", help="Export orchestrator state and proposals")
    loop_export.add_argument(
        "--out",
        type=Path,
        help="Optional path to write the combined export as JSON",
    )
    loop_export.set_defaults(func=_cmd_loop_export)

    timeline_parser = subparsers.add_parser(
        "timeline", help="Aggregate cycle, pulse, and puzzle relationships"
    )
    timeline_parser.add_argument(
        "--cycle",
        type=int,
        help="Render a single cycle timeline to stdout",
    )
    timeline_parser.add_argument(
        "--limit",
        type=int,
        help="Limit processing to the most recent N cycles",
    )
    timeline_parser.add_argument(
        "--amplify-log",
        type=Path,
        default=Path("state/amplify_log.jsonl"),
        help="Path to amplification history (default: state/amplify_log.jsonl)",
    )
    timeline_parser.add_argument(
        "--pulse-history",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to pulse history ledger (default: pulse_history.json)",
    )
    timeline_parser.add_argument(
        "--puzzle-index",
        type=Path,
        default=Path("data/puzzle_index.json"),
        help="Path to the puzzle index dataset (default: data/puzzle_index.json)",
    )
    timeline_parser.add_argument(
        "--out",
        type=Path,
        help="Directory to write exported artifacts (default: artifacts)",
    )
    timeline_parser.add_argument(
        "--project-root",
        type=Path,
        help="Repository root to resolve relative paths (default: current directory)",
    )
    timeline_parser.set_defaults(func=_cmd_timeline)

    pulse_parser = subparsers.add_parser("pulse", help="Pulse Weaver utilities")
    pulse_sub = pulse_parser.add_subparsers(dest="pulse_command", required=True)

    pulse_watch = pulse_sub.add_parser("watch", help="Run a watchdog remediation cycle")
    pulse_watch.add_argument("--reason", help="Override remediation reason")
    pulse_watch.add_argument("--dry-run", action="store_true", help="Dry-run only")
    pulse_watch.add_argument("--max-attempts", type=int, default=1)
    pulse_watch.add_argument("--cooldown-sec", type=int, default=0)
    pulse_watch.set_defaults(func=_cmd_pulse_watch)

    pulse_emit = pulse_sub.add_parser("emit", help="Emit a signed pulse event")
    pulse_emit.add_argument("repo")
    pulse_emit.add_argument("ref")
    pulse_emit.add_argument("--kind", required=True, choices=["merge", "fix", "doc", "schema"])
    pulse_emit.add_argument("--summary", required=True)
    pulse_emit.add_argument("--proof", required=True, help="Proof identifier")
    pulse_emit.add_argument("--state", type=Path, help="Override state directory")
    pulse_emit.add_argument("--key-file", type=Path, help="JSON file with signing key")
    pulse_emit.add_argument("--private-key", help="Hex encoded private key")
    pulse_emit.add_argument("--key-id", help="Identifier for the signing key")
    pulse_emit.add_argument("--public-key", help="Register public key when emitting")
    pulse_emit.add_argument("--dest", action="append", help="Optional webhook destinations")
    pulse_emit.set_defaults(func=_cmd_pulse_emit)

    pulse_history = pulse_sub.add_parser("history", help="Summarize pulse history events")
    pulse_history.add_argument("--path", type=Path, help="Override pulse history path")
    pulse_history.add_argument("--limit", type=int, help="Limit to the most recent N events")
    pulse_history.add_argument("--since", help="Only include events on/after this ISO timestamp")
    pulse_history.add_argument(
        "--aggregate",
        choices=sorted(AGGREGATE_SEGMENTS),
        help="Aggregate counts by a segment of the pulse message",
    )
    pulse_history.set_defaults(func=_cmd_pulse_history)

    ledger_parser = subparsers.add_parser("ledger", help="Temporal ledger commands")
    ledger_sub = ledger_parser.add_subparsers(dest="ledger_command", required=True)

    ledger_snapshot = ledger_sub.add_parser("snapshot", help="Export a ledger snapshot")
    ledger_snapshot.add_argument("--format", choices=["md", "svg"], default="md")
    ledger_snapshot.add_argument("--out", type=Path, help="Output directory")
    ledger_snapshot.add_argument("--state", type=Path, help="Override state directory")
    ledger_snapshot.add_argument("--since", help="ISO timestamp filter")
    ledger_snapshot.add_argument("--limit", type=int, default=50)
    ledger_snapshot.set_defaults(func=_cmd_ledger_snapshot)

    ledger_tail = ledger_sub.add_parser("tail", help="Print recent ledger entries")
    ledger_tail.add_argument("--state", type=Path, help="Override state directory")
    ledger_tail.add_argument("--since", help="ISO timestamp filter")
    ledger_tail.add_argument("--limit", type=int, default=10)
    ledger_tail.set_defaults(func=_cmd_ledger_tail)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
