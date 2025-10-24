"""Registry webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..origin_capsule import OriginCapsule
from ..registry_sync import RegistryLedger, apply_github_push


router = APIRouter(prefix="/api/registry", tags=["registry"])


@router.post("/webhook")
async def ingest_registry_webhook(request: Request) -> dict[str, object]:
    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        raise HTTPException(status_code=400, detail="Unsupported event type")
    payload = await request.json()
    ledger = RegistryLedger()
    capsule = OriginCapsule()
    updates = apply_github_push(payload, ledger=ledger, capsule=capsule)
    return {"updated": len(updates), "events": updates}


__all__ = ["router"]

