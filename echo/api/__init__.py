"""Echo API application."""

from __future__ import annotations

from fastapi import FastAPI

from .routes_atlas import router as atlas_router, value_error_handler
from .routes_echonet import router as echonet_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads

app = FastAPI(title="Echo")
app.include_router(echonet_router)
app.include_router(atlas_router)
app.add_exception_handler(ValueError, value_error_handler)

__all__ = [
    "app",
    "atlas_router",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
