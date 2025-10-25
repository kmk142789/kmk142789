"""Timeline routes exposing cycle, pulse, and puzzle aggregations."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from echo.timeline import build_cycle_timeline

router = APIRouter(prefix="/timeline", tags=["timeline"])


def _resolve_entries(limit: int | None = None):
    entries = build_cycle_timeline(
        project_root=Path.cwd(),
        limit=limit,
    )
    return entries


@router.get("/cycles")
def list_cycles(limit: int | None = Query(default=None, ge=1)) -> dict[str, object]:
    entries = _resolve_entries(limit=limit)
    return {
        "cycles": [entry.to_dict() for entry in entries],
        "count": len(entries),
    }


@router.get("/cycles/{cycle}")
def get_cycle(cycle: int) -> dict[str, object]:
    entries = _resolve_entries()
    for entry in entries:
        if entry.snapshot.cycle == cycle:
            payload = entry.to_dict()
            payload["cycle"] = entry.snapshot.cycle
            return payload
    raise HTTPException(status_code=404, detail="Cycle not found")


__all__ = ["router"]
