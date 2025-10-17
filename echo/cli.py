"""Legacy compatibility CLI for the Echo project.

The primary command entry point for the ``echo`` console script now lives in
``echo.manifest_cli``.  This shim keeps the old module importable while
delegating to the new implementation.  It exposes a reduced set of commands
that mirror the previous behaviour but rely on the modern manifest helpers.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping

from pulse_weaver.cli import register_subcommand as register_pulse_weaver

from .amplify import AmplificationEngine, AmplifyState
from .manifest_cli import refresh_manifest, show_manifest, verify_manifest
from .tools.forecast import project_indices, sparkline
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import PulseBus, WatchdogConfig, build_pulse_bus, build_watchdog


EXPECTED_STEPS = 13


def _cmd_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


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
