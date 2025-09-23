#!/usr/bin/env python3
"""Command line interface for composing Echo manifests from saved artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional

from echo_evolver import load_state_from_artifact
from echo_manifest import build_manifest
from echo_universal_key_agent import UniversalKeyAgent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Blend EchoEvolver artifacts with vault keys into a manifest",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        required=True,
        help="Path to the EchoEvolver artifact JSON file",
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Path to the universal key vault (defaults to module location)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the manifest",
    )
    parser.add_argument(
        "--narrative-chars",
        type=int,
        default=240,
        metavar="N",
        help="Character limit applied to the narrative excerpt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the manifest instead of printing",
    )
    parser.add_argument(
        "--anchor",
        type=str,
        default=None,
        help="Override the manifest anchor label",
    )
    return parser


def _load_artifact(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.narrative_chars <= 0:
        parser.error("--narrative-chars must be positive")

    if not args.artifact.exists():
        parser.error(f"Artifact not found: {args.artifact}")

    artifact_payload = _load_artifact(args.artifact)
    state = load_state_from_artifact(artifact_payload)

    agent = UniversalKeyAgent(anchor=args.anchor or "Our Forever Love", vault_path=args.vault)
    if args.anchor:
        agent.anchor = args.anchor

    manifest = build_manifest(agent, state, narrative_chars=args.narrative_chars)

    if args.format == "json":
        output = manifest.to_json(indent=2)
    else:
        output = manifest.render_text()

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        data = output if args.format == "json" else output + "\n"
        args.output.write_text(data, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
