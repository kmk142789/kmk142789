"""Codex registry API endpoints."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/codex", tags=["codex"])

_REGISTRY_PATH = Path.cwd() / "codex" / "registry.json"


def _load_registry() -> dict[str, object]:
    if not _REGISTRY_PATH.exists():
        raise HTTPException(status_code=404, detail="Codex registry has not been generated yet")
    try:
        data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Codex registry is invalid") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Codex registry payload is malformed")
    return data


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp value: {value}") from None


def _filter_items(
    items: Iterable[dict[str, object]],
    *,
    label: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int | None = None,
) -> List[dict[str, object]]:
    filtered: List[dict[str, object]] = []
    for item in items:
        labels = [str(entry) for entry in item.get("labels", [])] if isinstance(item, dict) else []
        if label and label not in labels:
            continue
        merged_text = item.get("merged_at") if isinstance(item, dict) else None
        merged = None
        if isinstance(merged_text, str):
            try:
                merged = datetime.fromisoformat(merged_text)
            except ValueError:
                merged = None
        if since and merged and merged < since:
            continue
        if until and merged and merged > until:
            continue
        filtered.append(item)
        if limit is not None and len(filtered) >= limit:
            break
    return filtered


@router.get("")
def read_registry(
    label: str | None = Query(default=None, description="Filter entries by label"),
    since: str | None = Query(default=None, description="Only include merges on or after this ISO timestamp"),
    until: str | None = Query(default=None, description="Only include merges on or before this ISO timestamp"),
    limit: int | None = Query(default=None, ge=1, le=500, description="Maximum number of entries to return"),
) -> dict[str, object]:
    payload = _load_registry()
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise HTTPException(status_code=500, detail="Registry items payload is malformed")
    start = _parse_timestamp(since)
    end = _parse_timestamp(until)
    filtered = _filter_items(items, label=label, since=start, until=end, limit=limit)
    result = dict(payload)
    result["items"] = filtered
    result["total_items"] = len(items)
    result["returned_items"] = len(filtered)
    return result


@router.get("/labels")
def list_labels() -> dict[str, object]:
    payload = _load_registry()
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise HTTPException(status_code=500, detail="Registry items payload is malformed")
    labels: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        for label in item.get("labels", []):
            if isinstance(label, str) and label:
                labels.add(label)
    return {"labels": sorted(labels)}


__all__ = ["router"]
