"""Capability planning API routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..cap.model import Capability, CapState
from ..cap.plan import plan_install
from ..cap.registry import load_catalog, load_state

router = APIRouter(prefix="/api/cap", tags=["capabilities"])


@router.post("/plan")
def plan(cap: Capability) -> dict:
    catalog = load_catalog()
    state = load_state()
    if cap.name not in catalog:
        catalog = {**catalog, cap.name: cap}
    steps = plan_install(cap, catalog, state)
    return {"count": len(steps), "steps": [c.name for c in steps]}


__all__ = ["router"]
