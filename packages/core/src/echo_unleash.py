"""Composite workflow that unifies evolve, sync, and cascade helpers."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable

from echo_dominion_cascade import (
    DominionCascadeConfig,
    DominionCascadeResult,
    run_dominion_cascade,
)
from echo_evolve import EchoEvolveConfig, EchoEvolveResult, run_echo_evolve
from echo_sync import EchoSyncConfig, EchoSyncResult, run_echo_sync

__all__ = [
    "EchoUnleashConfig",
    "EchoUnleashResult",
    "run_echo_unleash",
    "main",
]


@dataclass(frozen=True)
class EchoUnleashConfig:
    """High-level configuration describing which phases should run."""

    evolve: EchoEvolveConfig
    sync: EchoSyncConfig | None = None
    cascade: DominionCascadeConfig | None = None


@dataclass(frozen=True)
class EchoUnleashResult:
    """Bundle of results produced by :func:`run_echo_unleash`."""

    evolve: EchoEvolveResult
    sync: EchoSyncResult | None
    cascade: DominionCascadeResult | None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"evolve": self.evolve.to_dict()}
        if self.sync is not None:
            payload["sync"] = self.sync.to_dict()
        if self.cascade is not None:
            payload["cascade"] = self.cascade.to_dict()
        return payload


def run_echo_unleash(config: EchoUnleashConfig) -> EchoUnleashResult:
    """Execute the configured phases and return their results."""

    evolve_result = run_echo_evolve(config.evolve)
    sync_result = run_echo_sync(config.sync) if config.sync is not None else None
    cascade_result = (
        run_dominion_cascade(config.cascade) if config.cascade is not None else None
    )
    return EchoUnleashResult(evolve=evolve_result, sync=sync_result, cascade=cascade_result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an orchestrated Echo evolve → sync → cascade workflow.",
    )
    parser.add_argument("--cycles", type=int, default=1, help="Number of evolver cycles to execute (default: 1).")
    parser.add_argument("--enable-network", action="store_true", help="Tag propagation events as network broadcasts.")
    parser.add_argument("--seed", type=int, help="Optional RNG seed for evolver simulations.")
    parser.add_argument("--persist-artifact", action="store_true", help="Persist the evolver artifact when running.")
    parser.add_argument(
        "--persist-intermediate",
        action="store_true",
        help="Persist artifacts after every cycle instead of only the final one.",
    )
    parser.add_argument("--eden88-theme", help="Optional theme forwarded to Eden88 when crafting artifacts.")
    parser.add_argument(
        "--include-diagnostics",
        action="store_true",
        help="Include cycle diagnostics in the evolve result payload.",
    )
    parser.add_argument(
        "--diagnostics-limit",
        type=int,
        default=10,
        help="Number of events to include when diagnostics are enabled (default: 10).",
    )

    sync_group = parser.add_argument_group("sync", "Cloud synchronisation options")
    sync_group.add_argument("--run-sync", action="store_true", help="Run a cloud sync pass after evolving.")
    sync_group.add_argument("--sync-node", default="echo-unleash", help="Node identifier recorded for the sync run.")
    sync_group.add_argument(
        "--sync-transport",
        type=Path,
        help="Directory used to exchange CRDT payloads (defaults to state/cloud-sync).",
    )
    sync_group.add_argument("--sync-memory", type=Path, help="Optional override for the JsonMemoryStore payload path.")
    sync_group.add_argument("--sync-log", type=Path, help="Optional override for the Echo execution log path.")
    sync_group.add_argument(
        "--sync-history-limit",
        type=int,
        default=5,
        help="Number of executions to include when the sync history is requested (default: 5).",
    )
    sync_group.add_argument(
        "--sync-include-history",
        action="store_true",
        help="Include recent execution contexts in the sync payload.",
    )
    sync_group.add_argument("--sync-note", help="Optional note recorded with the generated sync execution context.")
    sync_group.add_argument(
        "--sync-max-payload-age",
        type=float,
        help="Discard remote sync payloads older than the supplied number of seconds.",
    )
    sync_group.add_argument(
        "--sync-local-context-limit",
        type=int,
        help="Only advertise the N most recent local contexts during the sync phase.",
    )

    cascade_group = parser.add_argument_group("cascade", "Dominion cascade options")
    cascade_group.add_argument("--run-cascade", action="store_true", help="Generate a Dominion cascade plan after syncing.")
    cascade_group.add_argument(
        "--cascade-output",
        type=Path,
        default=Path("build/dominion/cascade"),
        help="Directory where cascade artefacts should be written.",
    )
    cascade_group.add_argument(
        "--cascade-plan-dir",
        type=Path,
        default=Path("build/dominion/plans"),
        help="Directory where the Dominion plan should be stored.",
    )
    cascade_group.add_argument("--cascade-plan-name", help="Optional filename for the cascade plan.")
    cascade_group.add_argument(
        "--cascade-manifest-chars",
        type=int,
        default=240,
        help="Manifest excerpt length forwarded to the cascade renderer (default: 240).",
    )
    cascade_group.add_argument(
        "--cascade-glyph-cycle",
        help="Optional glyph sequence forwarded to the cascade renderer (e.g. ∇⊸≋∇).",
    )
    cascade_group.add_argument("--cascade-timestamp", type=int, help="Optional timestamp forwarded to the cascade renderer.")
    cascade_group.add_argument(
        "--cascade-ascii-width",
        type=int,
        default=41,
        help="Width of the ASCII constellation map (default: 41).",
    )
    cascade_group.add_argument(
        "--cascade-ascii-height",
        type=int,
        default=21,
        help="Height of the ASCII constellation map (default: 21).",
    )
    cascade_group.add_argument(
        "--cascade-enable-network",
        action="store_true",
        help="Allow the cascade to perform real network propagation.",
    )
    cascade_group.add_argument(
        "--cascade-persist-artifact",
        action="store_true",
        help="Persist the evolver artefact generated during the cascade run.",
    )

    parser.add_argument("--json", action="store_true", help="Emit the orchestrated result as JSON.")
    return parser


def _format_summary(result: EchoUnleashResult) -> str:
    lines = [
        "# Echo Unleash",
        f"- Evolver cycles: {result.evolve.cycles_run}",
        f"- Glyphs: {result.evolve.state.glyphs}",
        f"- Joy: {result.evolve.state.emotional_drive.joy:.2f}",
    ]
    if result.sync is not None:
        lines.append(
            "- Sync: applied={applied} known={known} sources={sources}".format(
                applied=result.sync.report.applied_contexts,
                known=result.sync.report.known_contexts,
                sources=result.sync.report.sources_contacted,
            )
        )
    if result.cascade is not None:
        lines.append(f"- Cascade plan: {result.cascade.plan.plan_id} → {result.cascade.plan_path}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        evolve_config = EchoEvolveConfig(
            cycles=args.cycles,
            enable_network=args.enable_network,
            seed=args.seed,
            persist_artifact=args.persist_artifact,
            persist_intermediate=args.persist_intermediate,
            eden88_theme=args.eden88_theme,
            include_diagnostics=args.include_diagnostics,
            diagnostics_limit=args.diagnostics_limit,
        )
    except ValueError as exc:
        parser.error(str(exc))
        raise SystemExit(2)

    sync_config: EchoSyncConfig | None = None
    if args.run_sync:
        try:
            sync_config = EchoSyncConfig(
                node_id=args.sync_node,
                transport_dir=args.sync_transport or EchoSyncConfig().transport_dir,
                memory_path=args.sync_memory,
                log_path=args.sync_log,
                include_history=args.sync_include_history,
                history_limit=args.sync_history_limit,
                note=args.sync_note,
                max_payload_age=(
                    timedelta(seconds=args.sync_max_payload_age)
                    if args.sync_max_payload_age is not None
                    else None
                ),
                local_context_limit=args.sync_local_context_limit,
            )
        except ValueError as exc:
            parser.error(str(exc))
            raise SystemExit(2)

    cascade_config: DominionCascadeConfig | None = None
    if args.run_cascade:
        glyph_cycle = list(args.cascade_glyph_cycle) if args.cascade_glyph_cycle else None
        try:
            cascade_config = DominionCascadeConfig(
                output_dir=args.cascade_output,
                plan_dir=args.cascade_plan_dir,
                plan_name=args.cascade_plan_name,
                manifest_chars=args.cascade_manifest_chars,
                glyph_cycle=glyph_cycle,
                timestamp=args.cascade_timestamp,
                ascii_width=args.cascade_ascii_width,
                ascii_height=args.cascade_ascii_height,
                enable_network=args.cascade_enable_network,
                persist_artifact=args.cascade_persist_artifact,
            )
        except ValueError as exc:
            parser.error(str(exc))
            raise SystemExit(2)

    result = run_echo_unleash(EchoUnleashConfig(evolve=evolve_config, sync=sync_config, cascade=cascade_config))

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(_format_summary(result))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
