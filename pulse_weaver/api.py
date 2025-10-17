"""FastAPI router exposing Pulse Weaver snapshots."""

from __future__ import annotations

from fastapi import APIRouter

from .service import PulseWeaverService


def create_router(service: PulseWeaverService) -> APIRouter:
    router = APIRouter(prefix="/pulse/weaver", tags=["Pulse Weaver"])

    @router.get("", name="pulse_weaver_snapshot")
    def _snapshot() -> dict[str, object]:
        snapshot = service.snapshot().to_dict()
        return snapshot

    return router


__all__ = ["create_router"]
