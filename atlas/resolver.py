"""Resolution policies for merging universes."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List
import json

from .graph import FederationGraph


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def merge_universes(graph: FederationGraph, universes: Iterable[str], policy: str = "latest-wins") -> dict:
    """Merge artifacts from *universes* according to *policy*."""

    universes = list(universes)
    if not universes:
        raise ValueError("At least one universe must be provided")

    if policy != "latest-wins":
        raise ValueError(f"Unsupported merge policy: {policy}")

    merged: Dict[str, dict] = {}
    grouped: Dict[str, List[dict]] = defaultdict(list)

    for node in graph.artifacts:
        if node.universe not in universes:
            continue
        grouped[node.artifact_id].append(node.to_dict())

    for artifact_id, entries in grouped.items():
        if len(entries) == 1:
            merged[artifact_id] = entries[0]
            continue
        entries.sort(
            key=lambda entry: (
                _parse_timestamp(entry.get("timestamp")) or datetime.min,
                entry.get("universe"),
            ),
            reverse=True,
        )
        merged[artifact_id] = entries[0]

    return {
        "policy": policy,
        "universes": universes,
        "artifacts": merged,
    }


def save_merge(result: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with destination.joinpath("merged_state.json").open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
