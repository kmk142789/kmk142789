"""Echo API application."""

from __future__ import annotations

from fastapi import FastAPI

from .routes_echonet import router as echonet_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads

app = FastAPI(title="Echo")
app.include_router(echonet_router)

__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
