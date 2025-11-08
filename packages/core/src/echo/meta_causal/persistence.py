"""Persistence helpers for the meta causal awareness engine."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .types import MetaCausalSnapshot


def snapshot_to_json(snapshot: MetaCausalSnapshot, *, indent: int = 2) -> str:
    """Return *snapshot* encoded as formatted JSON."""

    return snapshot.to_json(indent=indent)


def write_snapshot(snapshot: MetaCausalSnapshot, path: Path, *, indent: int = 2) -> None:
    """Write *snapshot* to ``path`` in UTF-8 encoded JSON."""

    path.write_text(snapshot_to_json(snapshot, indent=indent), encoding="utf-8")


def load_snapshot(payload: Mapping[str, Any]) -> MetaCausalSnapshot:
    """Hydrate a :class:`MetaCausalSnapshot` from a dictionary payload."""

    created_at_raw = payload.get("created_at")
    created_at = (
        datetime.fromisoformat(created_at_raw)
        if isinstance(created_at_raw, str)
        else datetime.now(timezone.utc)
    )
    observations = tuple(payload.get("observations", ()))
    links = tuple(payload.get("links", ()))
    metrics = dict(payload.get("metrics", {}))
    digest = str(payload.get("digest", ""))
    anchor = str(payload.get("anchor", ""))
    return MetaCausalSnapshot(
        anchor=anchor,
        created_at=created_at,
        observations=observations,
        links=links,
        metrics=metrics,
        digest=digest,
    )


__all__ = ["snapshot_to_json", "write_snapshot", "load_snapshot"]

