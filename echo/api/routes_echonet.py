"""EchoNet-facing API routes."""

from __future__ import annotations

import time
from fastapi import APIRouter

from .state import dag, receipts, session_heads

router = APIRouter(prefix="/api/echonet")


@router.get("/ping")
def ping() -> dict[str, float | bool]:
    return {"ok": True, "ts": time.time()}


@router.get("/state")
def state() -> dict[str, object]:
    tip = receipts.tip()
    try:
        height = receipts.height(tip)
    except Exception:
        height = 0

    try:
        merkle = dag.merkle_root(session_heads())
    except Exception:
        merkle = "cid_0"

    return {"tip": tip, "height": height, "merkle": merkle}


__all__ = ["router"]
