"""Development ASGI application exposing the Echo identity bridge router."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI

from echo.bridge.router import create_router
from modules.echo-bridge.bridge_api import EchoBridgeAPI


@lru_cache(maxsize=1)
def _build_bridge_api() -> EchoBridgeAPI:
    """Create an :class:`EchoBridgeAPI` using environment configuration."""

    return EchoBridgeAPI(
        github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
        telegram_chat_id=os.getenv("ECHO_BRIDGE_TELEGRAM_CHAT_ID"),
        firebase_collection=os.getenv("ECHO_BRIDGE_FIREBASE_COLLECTION"),
    )


def create_app(*, bridge: Optional[EchoBridgeAPI] = None) -> FastAPI:
    """Instantiate the identity bridge API application."""

    app = FastAPI(title="Identity Bridge", version="0.1.0")
    bridge_api = bridge or _build_bridge_api()
    app.include_router(create_router(api=bridge_api))

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:  # pragma: no cover - runtime helper
        return {"status": "ok"}

    return app


app = create_app()


__all__ = ["app", "create_app"]
