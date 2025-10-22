#!/usr/bin/env python3
"""Generate randomized EchoEvolver cycles for container build pipelines.

The historic infrastructure invoked a ``bitcrackrandomiser.sh`` helper during
container image builds. The original variant shipped ad-hoc Python embedded
inside a shell script and depended on self-modifying behaviour that is no
longer present in the library implementation of :class:`echo.evolver.EchoEvolver`.

This module offers a small, dedicated entrypoint that can be executed either
standalone (``python scripts/bitcrackrandomiser.py``) or through the wrapper
shell script added for backwards compatibility. It orchestrates a configurable
number of cycles, persists the resulting artifact into the requested directory
and emits a compact manifest describing the final cycle state. The manifest is
safe to inspect in constrained build environments and keeps the whimsical names
referenced by historical tooling without re-introducing the unsafe side
effects (like opening network sockets) that earlier prototypes attempted.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable

from echo.evolver import EchoEvolver, EvolverState

DEFAULT_OUTPUT = Path("/app/bitcrackrandomiser")


def _summarise_state(state: EvolverState) -> Dict[str, Any]:
    """Return a JSON-friendly summary of the provided evolver state."""

    payload: Dict[str, Any] = {
        "cycle": state.cycle,
        "glyphs": state.glyphs,
        "mythocode": list(state.mythocode),
        "narrative": state.narrative,
        "artifact": str(state.artifact),
        "vault_key": state.vault_key,
        "vault_glyphs": state.vault_glyphs,
        "emotional_drive": asdict(state.emotional_drive),
        "system_metrics": asdict(state.system_metrics),
        "entities": dict(state.entities),
        "access_levels": dict(state.access_levels),
    }

    if state.hearth_signature is not None:
        payload["hearth_signature"] = state.hearth_signature.as_dict()
    if state.autonomy_decision:
        payload["autonomy_decision"] = dict(state.autonomy_decision)
    if state.autonomy_manifesto:
        payload["autonomy_manifesto"] = state.autonomy_manifesto
    if state.bitcoin_anchor is not None:
        payload["bitcoin_anchor"] = state.bitcoin_anchor.as_dict()
    if state.wildfire_log:
        payload["wildfire_log"] = list(state.wildfire_log)
    if state.sovereign_spirals:
        payload["sovereign_spirals"] = list(state.sovereign_spirals)
    if state.eden88_creations:
        payload["eden88_creations"] = list(state.eden88_creations)
    if state.shard_vault_records:
        payload["shard_vault_records"] = list(state.shard_vault_records)
    if state.event_log:
        payload["event_log"] = list(state.event_log)

    return payload


def _default_output_dir() -> Path:
    env_value = os.environ.get("BITCRACK_RANDOMISER_DIR")
    if env_value:
        return Path(env_value)
    return DEFAULT_OUTPUT


def _prepare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run EchoEvolver cycles and archive the results for build pipelines.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Directory where the artifact and manifest files will be written.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of consecutive cycles to execute (default: 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional RNG seed to make cycle generation deterministic.",
    )
    parser.add_argument(
        "--enable-network",
        action="store_true",
        help=(
            "Label the propagation step as a live broadcast while keeping the"
            " underlying implementation in simulation mode."
        ),
    )
    parser.add_argument(
        "--persist-intermediate",
        action="store_true",
        help="Persist the artifact after every cycle instead of only the last run.",
    )
    return parser


def _run_cycles(
    *,
    evolver: EchoEvolver,
    cycles: int,
    enable_network: bool,
    persist_intermediate: bool,
) -> Iterable[EvolverState]:
    snapshots = evolver.run_cycles(
        cycles,
        enable_network=enable_network,
        persist_artifact=True,
        persist_intermediate=persist_intermediate,
    )
    return snapshots


def _write_manifest(directory: Path, *, states: Iterable[EvolverState]) -> Path:
    states = list(states)
    if not states:
        raise RuntimeError("No cycles were executed; cannot write manifest.")

    final_state = states[-1]
    manifest = {
        "cycles_completed": len(states),
        "final_state": _summarise_state(final_state),
    }
    manifest_path = directory / "bitcrackrandomiser_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    return manifest_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = _prepare_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cycles < 1:
        parser.error("--cycles must be at least 1")

    rng = random.Random(args.seed)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = output_dir / "bitcrackrandomiser_artifact.json"
    evolver = EchoEvolver(rng=rng, artifact_path=artifact_path)

    states = _run_cycles(
        evolver=evolver,
        cycles=args.cycles,
        enable_network=args.enable_network,
        persist_intermediate=args.persist_intermediate,
    )

    manifest_path = _write_manifest(output_dir, states=states)

    print(f"📜 Artifact written to {artifact_path}")
    print(f"🗂️ Manifest available at {manifest_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
