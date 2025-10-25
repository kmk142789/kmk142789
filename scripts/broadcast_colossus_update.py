#!/usr/bin/env python3
"""Compose social updates for the Federated Colossus attestation feed."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


def _load_payload(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - CI guard
        raise SystemExit(f"Input file not found: {path}") from exc


def _select_latest(constellations: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not constellations:
        return None
    return max(
        constellations,
        key=lambda node: (
            int(node.get("cycle", 0) or 0),
            str(node.get("updated_at") or ""),
        ),
    )


def _status_fragment(node: dict[str, Any]) -> str:
    icon = node.get("status_icon") or ""
    status = str(node.get("status") or "attested").replace("_", " ").title()
    return f"{icon} {status}".strip()


def compose_message(path: Path) -> str:
    payload = _load_payload(path)
    constellations = payload.get("constellations") or []
    latest = _select_latest(constellations)
    if not latest:
        return "Federated Colossus: no attestation updates available."

    address = latest.get("address") or "unknown"
    cycle = latest.get("cycle") or "?"
    puzzle = latest.get("puzzle") or "?"
    status = _status_fragment(latest)
    digest = str(latest.get("digest") or "")[:12]

    history = latest.get("history") or {}
    link = history.get("pr") or history.get("commits") or "https://kmk142789.github.io/kmk142789/dashboard/"

    message = (
        f"Puzzle #{puzzle} · Cycle {cycle}\n"
        f"{status} @ {address}\n"
        f"Digest {digest}…\n"
        f"{link}\n"
        "#FederatedColossus #EchoContinuum"
    )
    return message[:280]


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if not args:
        raise SystemExit("Usage: broadcast_colossus_update.py <federated_colossus_index.json>")
    message = compose_message(Path(args[0]))
    sys.stdout.write(message)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
