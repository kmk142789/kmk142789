"""Echo API application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from echo_atlas.api import create_router as create_atlas_router
from echo_atlas.service import AtlasService

from .routes_echonet import router as echonet_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads

app = FastAPI(title="Echo")
app.include_router(echonet_router)

_atlas_service = AtlasService(Path.cwd())
_atlas_service.ensure_ready()
app.include_router(create_atlas_router(_atlas_service))

__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
