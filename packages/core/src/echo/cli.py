"""Unified Echo CLI exposing evolution, manifest, and orchestration helpers.

This module now powers the ``echo`` console script directly.  It retains the
manifest-focused commands provided by :mod:`echo.manifest_cli` while also
exposing the broader orchestration surface (``echo evolve``, semantic
negotiation, timeline refreshes, etc.).  The legacy manifest CLI remains
importable as :mod:`echo.manifest_cli` for workflows that require the narrower
interface.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, NoReturn, Sequence

from pulse_weaver.cli import register_subcommand as register_pulse_weaver

from .amplify import AmplificationEngine, AmplifyState
from .evolver import EchoEvolver, _MOMENTUM_SENSITIVITY
from .echo_evolver_satellite import SatelliteEchoEvolver
from .manifest_cli import refresh_manifest, show_manifest, verify_manifest
from .timeline import build_cycle_timeline, refresh_cycle_timeline
from .tools.forecast import project_indices, sparkline
from .tools.resonance_index import compute_resonance_fingerprint
from .novelty import NoveltyGenerator
from .semantic_negotiation import (
    NegotiationIntent,
    NegotiationParticipant,
    NegotiationRole,
    NegotiationSignal,
    NegotiationStage,
    SemanticNegotiationResolver,
)
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import PulseBus, WatchdogConfig, build_pulse_bus, build_watchdog
from echo.pulseweaver.fabric import FabricOperations
from echo.pulse import forecast_pulse_activity, load_pulse_events


EXPECTED_STEPS = 13

AGGREGATE_SEGMENTS = {
    "category": 0,
    "source": 1,
    "detail": 2,
}

NEGOTIATION_STATE_DIR = Path("state/orchestrator/negotiations")


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _bounded_sentiment(value: str) -> float:
    score = float(value)
    if score < -1.0 or score > 1.0:
        raise argparse.ArgumentTypeError("sentiment must be between -1.0 and 1.0")
    return score


def _build_negotiation_resolver(path: Path | None) -> SemanticNegotiationResolver:
    state_dir = Path(path or NEGOTIATION_STATE_DIR)
    state_dir.mkdir(parents=True, exist_ok=True)
    return SemanticNegotiationResolver(state_dir=state_dir)


def _parse_negotiation_participant(spec: str) -> NegotiationParticipant:
    tokens = [token.strip() for token in spec.split(":")]
    if not tokens or not tokens[0]:
        raise argparse.ArgumentTypeError("participant specification requires an identifier")
    identifier = tokens[0]
    role_token = tokens[1] if len(tokens) > 1 and tokens[1] else NegotiationRole.OBSERVER.value
    alias = tokens[2] if len(tokens) > 2 and tokens[2] else None
    try:
        role = NegotiationRole(role_token)
    except ValueError as exc:  # pragma: no cover - defensive validation
        raise argparse.ArgumentTypeError(f"invalid participant role '{role_token}'") from exc
    return NegotiationParticipant(participant_id=identifier, role=role, alias=alias)


def _apply_capabilities(
    participants: Sequence[NegotiationParticipant], capability_specs: Sequence[str]
) -> list[NegotiationParticipant]:
    if not capability_specs:
        return [participant for participant in participants]
    capability_map: dict[str, list[str]] = {}
    for spec in capability_specs:
        if "=" not in spec:
            raise argparse.ArgumentTypeError("capabilities must use participant=capability format")
        participant_id, value = spec.split("=", 1)
        participant_id = participant_id.strip()
        value = value.strip()
        if not participant_id or not value:
            raise argparse.ArgumentTypeError("capabilities must include participant and value")
        capability_map.setdefault(participant_id, []).append(value)
    enriched: list[NegotiationParticipant] = []
    for participant in participants:
        caps = capability_map.get(participant.participant_id)
        if caps:
            enriched.append(participant.model_copy(update={"capabilities": caps}))
        else:
            enriched.append(participant)
    return enriched


def _cmd_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    show_manifest(args.path)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def _cmd_satellite(args: argparse.Namespace) -> int:
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(message)s")

    evolver = SatelliteEchoEvolver(artifact_path=args.artifact, seed=args.seed)
    if args.cycle is not None:
        evolver.state.cycle = args.cycle

    evolver.run(
        enable_network=args.network,
        emit_report=args.propagation_report,
        emit_resilience=args.resilience_report,
    )
    return 0


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
    if args.advance_system and args.describe_sequence_json:
        parser_error("--advance-system cannot be combined with --describe-sequence-json")
    if args.advance_system and args.persist_intermediate:
        parser_error("--advance-system cannot be combined with --persist-intermediate")

    if args.include_event_summary and args.event_summary_limit <= 0:
        parser_error("--event-summary-limit must be positive when including the event summary")
    if args.include_system_report and args.system_report_events <= 0:
        parser_error("--system-report-events must be positive when including the system report")
    if args.include_diagnostics and args.diagnostics_window <= 0:
        parser_error("--diagnostics-window must be positive when including diagnostics")
    if args.advance_system and args.momentum_window <= 0:
        parser_error("--momentum-window must be positive when using --advance-system")
    if args.advance_system and args.momentum_threshold <= 0:
        parser_error("--momentum-threshold must be positive when using --advance-system")
    if args.manifest_events < 0:
        parser_error("--manifest-events must be non-negative")

    if not args.advance_system:
        default_summary_limit = parser.get_default("event_summary_limit") if parser else 5
        if args.event_summary_limit != default_summary_limit:
            parser_error("--event-summary-limit requires --advance-system")

        default_system_events = parser.get_default("system_report_events") if parser else 5
        if args.system_report_events != default_system_events:
            parser_error("--system-report-events requires --advance-system")
        default_diagnostics_window = parser.get_default("diagnostics_window") if parser else 5
        if args.diagnostics_window != default_diagnostics_window:
            parser_error("--diagnostics-window requires --advance-system")

        default_momentum_window = parser.get_default("momentum_window") if parser else 5
        if args.momentum_window != default_momentum_window:
            parser_error("--momentum-window requires --advance-system")
        default_momentum_threshold = (
            parser.get_default("momentum_threshold") if parser else _MOMENTUM_SENSITIVITY
        )
        if args.momentum_threshold != default_momentum_threshold:
            parser_error("--momentum-threshold requires --advance-system")

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
    if args.diagnostics_window > 0 and not args.include_diagnostics:
        default_diagnostics_window = parser.get_default("diagnostics_window") if parser else 5
        if args.diagnostics_window != default_diagnostics_window:
            parser_error("--diagnostics-window requires --include-diagnostics")

    if args.momentum_window > 0 and not args.advance_system:
        default_momentum_window = parser.get_default("momentum_window") if parser else 5
        if args.momentum_window != default_momentum_window:
            parser_error("--momentum-window requires --advance-system")
    if args.momentum_threshold > 0 and not args.advance_system:
        default_momentum_threshold = (
            parser.get_default("momentum_threshold") if parser else _MOMENTUM_SENSITIVITY
        )
        if args.momentum_threshold != default_momentum_threshold:
            parser_error("--momentum-threshold requires --advance-system")

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
            or args.include_diagnostics
            or args.include_momentum_resonance
            or args.include_momentum_history
            or args.include_expansion_history
        )
    ):
        parser_error(
            "--include-matrix, --include-event-summary, --include-propagation, --include-system-report, "
            "--include-diagnostics, --include-momentum-resonance, --include-momentum-history, and "
            "--include-expansion-history require --advance-system"
        )

    if args.expansion_history_limit is not None:
        if args.expansion_history_limit <= 0:
            parser_error("--expansion-history-limit must be positive when provided")
        if not args.include_expansion_history:
            parser_error("--expansion-history-limit requires --include-expansion-history")
        if not args.advance_system:
            parser_error("--expansion-history-limit requires --advance-system")

    evolver = EchoEvolver(rng=rng, artifact_path=artifact_path)

    if args.describe_sequence:
        print(evolver.describe_sequence(persist_artifact=persist_artifact))
        return 0
    if args.describe_sequence_json:
        plan = evolver.sequence_plan(persist_artifact=persist_artifact)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
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
            include_diagnostics=args.include_diagnostics,
            include_momentum_resonance=args.include_momentum_resonance,
            include_momentum_history=args.include_momentum_history,
            event_summary_limit=args.event_summary_limit,
            manifest_events=args.manifest_events,
            system_report_events=args.system_report_events,
            diagnostics_window=args.diagnostics_window,
            momentum_window=args.momentum_window,
            momentum_threshold=args.momentum_threshold,
            include_expansion_history=args.include_expansion_history,
            expansion_history_limit=args.expansion_history_limit,
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


def _cmd_negotiation_open(args: argparse.Namespace) -> int:
    resolver = _build_negotiation_resolver(args.state_dir)
    participants = [_parse_negotiation_participant(item) for item in args.participant]
    if not participants:
        print("At least one participant must be provided with --participant")
        return 2
    participants = _apply_capabilities(participants, args.capability)
    intent = NegotiationIntent(
        topic=args.topic,
        summary=args.summary,
        tags=args.tag,
        desired_outcome=args.desired_outcome,
        priority=args.priority,
    )
    metadata: dict[str, str] = {}
    if args.note:
        metadata["note"] = args.note
    state = resolver.initiate(
        intent=intent,
        participants=participants,
        actor=args.actor,
        metadata=metadata,
    )
    payload = state.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"Negotiation {payload['negotiation_id']} opened at {payload['created_at']} :: "
            f"{intent.topic} [{payload['stage']}]"
        )
        print(f"Summary: {intent.summary}")
        if intent.tags:
            print(f"Tags: {', '.join(intent.tags)}")
        print("Participants:")
        for participant in payload.get("participants", []):
            caps = participant.get("capabilities") or []
            capability_text = f" capabilities={', '.join(caps)}" if caps else ""
            alias = f" ({participant.get('alias')})" if participant.get("alias") else ""
            print(
                f"  - {participant.get('participant_id')} as {participant.get('role')}{alias}{capability_text}"
            )
    return 0


def _cmd_negotiation_list(args: argparse.Namespace) -> int:
    resolver = _build_negotiation_resolver(args.state_dir)
    snapshot = resolver.snapshot(include_closed=args.include_closed)
    payload = snapshot.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        totals = payload.get("totals", {})
        print(
            "Negotiations :: "
            f"active {payload.get('active', 0)} | closed {payload.get('closed', 0)} | "
            f"opened {totals.get('opened', 0)} | signals {totals.get('signals', 0)}"
        )
        if not payload.get("observations"):
            print("No negotiations in the selected view.")
        for observation in payload.get("observations", []):
            outstanding = observation.get("outstanding_actions") or []
            sentiment = observation.get("sentiment_score", 0.0)
            print(
                f"- {observation.get('negotiation_id')} :: {observation.get('topic')} "
                f"[{observation.get('stage')}] sentiment {sentiment:+.2f}"
            )
            if outstanding:
                print(f"    outstanding: {', '.join(outstanding)}")
    return 0


def _cmd_negotiation_advance(args: argparse.Namespace) -> int:
    resolver = _build_negotiation_resolver(args.state_dir)
    try:
        stage = NegotiationStage(args.stage)
    except ValueError:
        print(f"Unknown negotiation stage: {args.stage}")
        return 2
    metadata: dict[str, str] = {}
    if args.note:
        metadata["note"] = args.note
    try:
        state = resolver.transition(
            args.negotiation_id,
            stage,
            actor=args.actor,
            reason=args.reason,
            metadata=metadata,
        )
    except KeyError:
        print(f"Negotiation {args.negotiation_id} not found")
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1
    payload = state.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"Negotiation {payload['negotiation_id']} stage -> {payload['stage']} "
            f"by {args.actor}"
        )
    return 0


def _cmd_negotiation_signal(args: argparse.Namespace) -> int:
    resolver = _build_negotiation_resolver(args.state_dir)
    payload: dict[str, str] = {}
    for entry in args.data:
        if "=" not in entry:
            print("Signal metadata must use key=value format")
            return 2
        key, value = entry.split("=", 1)
        payload[key.strip()] = value.strip()
    signal = NegotiationSignal(
        author=args.author,
        channel=args.channel,
        sentiment=args.sentiment,
        summary=args.summary,
        payload=payload,
    )
    try:
        state = resolver.record_signal(args.negotiation_id, signal)
    except KeyError:
        print(f"Negotiation {args.negotiation_id} not found")
        return 1
    payload_state = state.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload_state, indent=2, ensure_ascii=False))
    else:
        print(
            f"Signal recorded for {payload_state['negotiation_id']} via {args.channel} "
            f"sentiment={args.sentiment if args.sentiment is not None else '∅'}"
        )
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


def _cmd_resonance_fingerprint(args: argparse.Namespace) -> int:
    window = max(2, args.window)
    fingerprint = compute_resonance_fingerprint(
        args.series, window=window, label=args.label
    )
    payload = fingerprint.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    windowed = args.series[-window:]
    print(f"Glyph: {fingerprint.glyph} | Signature: {fingerprint.signature}")
    print(
        "Baseline: {baseline:.3f} | Velocity: {velocity:.3f} | Curvature: {curvature:.3f}".format(
            baseline=fingerprint.baseline,
            velocity=fingerprint.velocity,
            curvature=fingerprint.curvature,
        )
    )
    print(
        "Inversions: {inversions} | Coherence: {coherence:.3f} | Rarity: {rarity:.3f}".format(
            inversions=fingerprint.inversion_points,
            coherence=fingerprint.coherence,
            rarity=fingerprint.rarity,
        )
    )

    line = sparkline(windowed, width=min(32, len(windowed)))
    print(f"window[{len(windowed)}]: {', '.join(f'{value:.2f}' for value in windowed)}")
    if line:
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


def _cmd_pulse_forecast(args: argparse.Namespace) -> int:
    history_path = args.history
    if not history_path.exists():
        print(f"No pulse history found at {history_path}")
        return 1

    events = load_pulse_events(history_path)
    forecast = forecast_pulse_activity(
        events,
        horizon_hours=args.horizon_hours,
        warning_hours=args.warning_hours,
        critical_hours=args.critical_hours,
    )

    if args.json:
        print(json.dumps(forecast.to_dict(), indent=2, sort_keys=True))
        return 0

    print(forecast.to_report())
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


def _cmd_ledger_consensus(args: argparse.Namespace) -> int:
    parser: argparse.ArgumentParser | None = getattr(args, "_parser", None)
    if not (args.approve or args.reject or args.abstain):
        if parser is not None:
            parser.error("At least one participant vote must be supplied via --approve/--reject/--abstain")
        raise SystemExit(2)

    state_dir = args.state or Path("state")
    ledger = TemporalLedger(state_dir=state_dir)
    fabric = FabricOperations(state_dir=state_dir)
    result = fabric.trigger_consensus_round(
        ledger,
        topic=args.topic,
        initiator=args.initiator,
        quorum=args.quorum,
        approvals=args.approve,
        rejections=args.reject,
        abstentions=args.abstain,
    )
    payload = result.model_dump(mode="json")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _cmd_ledger_quorum(args: argparse.Namespace) -> int:
    state_dir = args.state or Path("state")
    fabric = FabricOperations(state_dir=state_dir)
    snapshot = fabric.quorum_health(window=args.window)
    payload = snapshot.model_dump(mode="json")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _cmd_ledger_diagnostics(args: argparse.Namespace) -> int:
    if args.limit is not None and args.limit <= 0:
        parser: argparse.ArgumentParser | None = getattr(args, "_parser", None)
        if parser is not None:
            parser.error("--limit must be a positive integer")
        raise SystemExit(2)

    state_dir = args.state or Path("state")
    fabric = FabricOperations(state_dir=state_dir)
    report = fabric.diagnostics(limit=args.limit)
    if args.format == "json":
        payload = report.model_dump(mode="json")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    payload = report.model_dump(mode="json")
    lines = [
        "# Fabric Diagnostics",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Total rounds: {payload['total_rounds']}",
        f"- Quorum met: {payload['quorum_met']}",
        f"- Quorum failed: {payload['quorum_failed']}",
        f"- Average consensus: {payload['average_consensus']}",
        "",
        "## Recent rounds",
    ]
    rounds = payload.get("rounds", [])
    if rounds:
        for round_payload in rounds:
            lines.append(
                f"- **{round_payload['recorded_at']}** — {round_payload['topic']} ({round_payload['round_id']})"
            )
            lines.append(
                "  - approvals: {approve}, rejections: {reject}, abstentions: {abstain}".format(
                    approve=len(round_payload.get("approvals", [])),
                    reject=len(round_payload.get("rejections", [])),
                    abstain=len(round_payload.get("abstentions", [])),
                )
            )
            lines.append(
                "  - consensus: {consensus}, quorum_met: {quorum}".format(
                    consensus=round_payload.get("consensus"),
                    quorum=round_payload.get("quorum_met"),
                )
            )
    else:
        lines.append("_No rounds recorded._")
    print("\n".join(lines))
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

    satellite_parser = subparsers.add_parser(
        "satellite", help="Run a SatelliteEchoEvolver cycle"
    )
    satellite_parser.add_argument("--artifact", type=Path, help="Artifact output path")
    satellite_parser.add_argument("--cycle", type=int, default=None, help="Starting cycle")
    satellite_parser.add_argument("--seed", type=int, default=None, help="Deterministic seed")
    satellite_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    satellite_parser.add_argument(
        "--network",
        action="store_true",
        help="Include network propagation events (simulated safety mode)",
    )
    satellite_parser.add_argument(
        "--propagation-report",
        action="store_true",
        help="Log the propagation report with per-channel details",
    )
    satellite_parser.add_argument(
        "--resilience-report",
        action="store_true",
        help="Log the resilience score and recommendations",
    )
    satellite_parser.set_defaults(func=_cmd_satellite)

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
    describe_group = evolve_parser.add_mutually_exclusive_group()
    describe_group.add_argument(
        "--describe-sequence",
        action="store_true",
        help=(
            "Render the recommended ritual sequence and exit without running a cycle."
        ),
    )
    describe_group.add_argument(
        "--describe-sequence-json",
        action="store_true",
        help=(
            "Emit the recommended ritual sequence as JSON and exit without running a cycle."
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
        "--include-diagnostics",
        action="store_true",
        help=(
            "Include the system diagnostics snapshot when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-momentum-resonance",
        action="store_true",
        help=(
            "Include the glyph-rich momentum resonance digest when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-momentum-history",
        action="store_true",
        help=(
            "Include the raw momentum history samples when using --advance-system."
        ),
    )
    evolve_parser.add_argument(
        "--include-expansion-history",
        action="store_true",
        help=(
            "Include the cached expansion history snapshots when using --advance-system."
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
        "--diagnostics-window",
        type=int,
        default=5,
        help=(
            "Number of diagnostics snapshots to retain when using --include-diagnostics "
            "(default: 5)."
        ),
    )
    evolve_parser.add_argument(
        "--momentum-window",
        type=int,
        default=5,
        help=(
            "Number of momentum samples to retain when using --advance-system "
            "(default: 5)."
        ),
    )
    evolve_parser.add_argument(
        "--momentum-threshold",
        type=float,
        default=_MOMENTUM_SENSITIVITY,
        help=(
            "Momentum sensitivity threshold used to classify acceleration when "
            "using --advance-system (default: {:.2f}).".format(
                _MOMENTUM_SENSITIVITY
            )
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
        "--expansion-history-limit",
        type=int,
        default=None,
        help=(
            "Optional limit for the embedded expansion history when using "
            "--include-expansion-history."
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

    negotiation_parser = subparsers.add_parser(
        "semantic-negotiation",
        help="Manage the semantic negotiation engine",
    )
    negotiation_sub = negotiation_parser.add_subparsers(
        dest="negotiation_command", required=True
    )

    negotiation_open = negotiation_sub.add_parser(
        "open", help="Initiate a new semantic negotiation"
    )
    negotiation_open.add_argument("--topic", required=True, help="Negotiation topic")
    negotiation_open.add_argument(
        "--summary", required=True, help="High-level summary for the negotiation"
    )
    negotiation_open.add_argument(
        "--participant",
        action="append",
        default=[],
        help="Participant spec formatted as id[:role][:alias]",
    )
    negotiation_open.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Assign a capability using participant=capability",
    )
    negotiation_open.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Attach an optional tag to the negotiation intent",
    )
    negotiation_open.add_argument(
        "--desired-outcome",
        dest="desired_outcome",
        help="Describe the desired outcome for the negotiation",
    )
    negotiation_open.add_argument(
        "--priority",
        help="Optional priority indicator for the negotiation",
    )
    negotiation_open.add_argument(
        "--actor",
        default="operator",
        help="Actor recorded for initiation events",
    )
    negotiation_open.add_argument(
        "--note",
        help="Attach an operator note to the initiation metadata",
    )
    negotiation_open.add_argument(
        "--state-dir",
        type=Path,
        default=NEGOTIATION_STATE_DIR,
        help="Directory used to persist negotiation state",
    )
    negotiation_open.add_argument(
        "--json",
        action="store_true",
        help="Emit the resulting state as JSON",
    )
    negotiation_open.set_defaults(func=_cmd_negotiation_open)

    negotiation_list = negotiation_sub.add_parser(
        "list", help="List active or historical negotiations"
    )
    negotiation_list.add_argument(
        "--include-closed",
        action="store_true",
        help="Include negotiations that have already resolved",
    )
    negotiation_list.add_argument(
        "--state-dir",
        type=Path,
        default=NEGOTIATION_STATE_DIR,
        help="Directory used to persist negotiation state",
    )
    negotiation_list.add_argument(
        "--json",
        action="store_true",
        help="Emit the snapshot as JSON",
    )
    negotiation_list.set_defaults(func=_cmd_negotiation_list)

    negotiation_advance = negotiation_sub.add_parser(
        "advance", help="Advance the stage for a negotiation"
    )
    negotiation_advance.add_argument("negotiation_id", help="Negotiation identifier")
    negotiation_advance.add_argument(
        "stage",
        choices=[stage.value for stage in NegotiationStage],
        help="Target negotiation stage",
    )
    negotiation_advance.add_argument(
        "--actor",
        default="operator",
        help="Actor recorded for the stage transition",
    )
    negotiation_advance.add_argument(
        "--reason",
        help="Optional reason describing the stage change",
    )
    negotiation_advance.add_argument(
        "--note",
        help="Attach an operator note to the transition metadata",
    )
    negotiation_advance.add_argument(
        "--state-dir",
        type=Path,
        default=NEGOTIATION_STATE_DIR,
        help="Directory used to persist negotiation state",
    )
    negotiation_advance.add_argument(
        "--json",
        action="store_true",
        help="Emit the updated state as JSON",
    )
    negotiation_advance.set_defaults(func=_cmd_negotiation_advance)

    negotiation_signal = negotiation_sub.add_parser(
        "signal", help="Record a signal influencing a negotiation"
    )
    negotiation_signal.add_argument("negotiation_id", help="Negotiation identifier")
    negotiation_signal.add_argument(
        "--channel",
        required=True,
        help="Channel or source describing the signal",
    )
    negotiation_signal.add_argument(
        "--author",
        default="operator",
        help="Actor responsible for the signal entry",
    )
    negotiation_signal.add_argument(
        "--summary",
        help="Human readable description of the signal",
    )
    negotiation_signal.add_argument(
        "--sentiment",
        type=_bounded_sentiment,
        default=None,
        help="Optional sentiment score between -1.0 and 1.0",
    )
    negotiation_signal.add_argument(
        "--data",
        action="append",
        default=[],
        help="Attach additional metadata using key=value",
    )
    negotiation_signal.add_argument(
        "--state-dir",
        type=Path,
        default=NEGOTIATION_STATE_DIR,
        help="Directory used to persist negotiation state",
    )
    negotiation_signal.add_argument(
        "--json",
        action="store_true",
        help="Emit the updated state as JSON",
    )
    negotiation_signal.set_defaults(func=_cmd_negotiation_signal)

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

    resonance_parser = subparsers.add_parser(
        "resonance-fingerprint", help="Synthesize a resonance glyph from a numeric series"
    )
    resonance_parser.add_argument(
        "series", type=float, nargs="+", help="Numeric samples representing a ritual window"
    )
    resonance_parser.add_argument(
        "--window",
        type=_positive_int,
        default=5,
        help="Window length used when computing the fingerprint (minimum 2)",
    )
    resonance_parser.add_argument(
        "--label",
        help="Optional label folded into the signature for reproducibility",
    )
    resonance_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the fingerprint payload as JSON instead of text",
    )
    resonance_parser.set_defaults(func=_cmd_resonance_fingerprint)

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

    pulse_forecast = pulse_sub.add_parser(
        "forecast", help="Project pulse cadence and risk across a planning horizon"
    )
    pulse_forecast.add_argument(
        "--history",
        type=Path,
        default=Path("pulse_history.json"),
        help="Path to pulse history ledger (default: pulse_history.json)",
    )
    pulse_forecast.add_argument(
        "--horizon-hours",
        type=float,
        default=168.0,
        help="Lookahead window for projected cadence (default: 168h / 7 days)",
    )
    pulse_forecast.add_argument(
        "--warning-hours",
        type=float,
        default=24.0,
        help="Warning threshold for stale cadence (default: 24h)",
    )
    pulse_forecast.add_argument(
        "--critical-hours",
        type=float,
        default=72.0,
        help="Critical threshold for stale cadence (default: 72h)",
    )
    pulse_forecast.add_argument("--json", action="store_true", help="Emit JSON output")
    pulse_forecast.set_defaults(func=_cmd_pulse_forecast)

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

    ledger_consensus = ledger_sub.add_parser(
        "consensus", help="Trigger a Fabric consensus round"
    )
    ledger_consensus.add_argument("--state", type=Path, help="Override state directory")
    ledger_consensus.add_argument("--topic", required=True, help="Topic or reference for the round")
    ledger_consensus.add_argument("--initiator", default="cli", help="Actor initiating the round")
    ledger_consensus.add_argument("--quorum", type=_positive_int, default=1)
    ledger_consensus.add_argument(
        "--approve",
        nargs="*",
        default=[],
        help="Participants approving the proposal",
    )
    ledger_consensus.add_argument(
        "--reject",
        nargs="*",
        default=[],
        help="Participants rejecting the proposal",
    )
    ledger_consensus.add_argument(
        "--abstain",
        nargs="*",
        default=[],
        help="Participants abstaining from the proposal",
    )
    ledger_consensus.set_defaults(func=_cmd_ledger_consensus, _parser=ledger_consensus)

    ledger_quorum = ledger_sub.add_parser(
        "quorum", help="Inspect Fabric quorum health"
    )
    ledger_quorum.add_argument("--state", type=Path, help="Override state directory")
    ledger_quorum.add_argument("--window", type=_positive_int, default=10)
    ledger_quorum.set_defaults(func=_cmd_ledger_quorum)

    ledger_diagnostics = ledger_sub.add_parser(
        "fabric-diagnostics", help="Export Fabric diagnostics"
    )
    ledger_diagnostics.add_argument("--state", type=Path, help="Override state directory")
    ledger_diagnostics.add_argument("--limit", type=int, help="Limit rounds included in the export")
    ledger_diagnostics.add_argument("--format", choices=["json", "md"], default="json")
    ledger_diagnostics.set_defaults(func=_cmd_ledger_diagnostics, _parser=ledger_diagnostics)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
