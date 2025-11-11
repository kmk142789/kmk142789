from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


__all__ = ["router"]
