from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..models import Base, get_engine
from .routes_files import router as files_router
from .routes_health import router as health_router


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):  # pragma: no cover - invoked by ASGI lifecycle
        Base.metadata.create_all(bind=get_engine())
        yield

    app = FastAPI(title="Vault v1", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(files_router)
    return app


def get_app() -> FastAPI:
    return create_app()


app = create_app()


__all__ = ["app", "create_app", "get_app"]
