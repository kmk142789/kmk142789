"""Echo API application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from echo_atlas.api import create_router as create_atlas_router
from echo_atlas.service import AtlasService
from pulse_weaver.api import create_router as create_pulse_weaver_router
from pulse_weaver.service import PulseWeaverService

from .routes_echonet import router as echonet_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import build_pulse_bus, build_watchdog
from echo.pulseweaver.api import create_router as create_pulse_router

app = FastAPI(title="Echo")
app.include_router(echonet_router)

_atlas_service = AtlasService(Path.cwd())
_atlas_service.ensure_ready()
app.include_router(create_atlas_router(_atlas_service))

_pulse_weaver_service = PulseWeaverService(Path.cwd())
_pulse_weaver_service.ensure_ready()
app.include_router(create_pulse_weaver_router(_pulse_weaver_service))

_pulse_watchdog = build_watchdog(Path.cwd() / "state")
_pulse_bus = build_pulse_bus(Path.cwd() / "state")
_pulse_ledger = TemporalLedger(state_dir=Path.cwd() / "state")
app.include_router(create_pulse_router(_pulse_watchdog, _pulse_bus, _pulse_ledger))

__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
