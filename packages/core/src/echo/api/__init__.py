"""Echo API application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from echo.bridge.router import create_router as create_bridge_router
from echo.pulsenet import PulseNetGatewayService
from echo.pulsenet.api import create_router as create_pulsenet_router
from echo.pulsenet.persistence import PulseEventStore
from echo.pulsenet.registration import RegistrationStore
from echo.pulsenet.stream import PulseAttestor, PulseHistoryStreamer
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
app.include_router(create_bridge_router())

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

_pulsenet_state = Path.cwd() / "state" / "pulsenet"
_pulsenet_state.mkdir(parents=True, exist_ok=True)
_pulsenet_store = RegistrationStore(_pulsenet_state / "registrations.json")
_pulsenet_events = PulseEventStore(_pulsenet_state / "pulse_events.db")
_pulsenet_stream = PulseHistoryStreamer(Path.cwd() / "pulse_history.json")
_pulsenet_attestor = PulseAttestor(TemporalLedger(state_dir=_pulsenet_state))
_pulsenet_service = PulseNetGatewayService(
    project_root=Path.cwd(),
    registration_store=_pulsenet_store,
    event_store=_pulsenet_events,
    pulse_streamer=_pulsenet_stream,
    attestor=_pulsenet_attestor,
    atlas_service=_atlas_service,
    resolver_config=_pulsenet_state / "resolver_sources.json",
)
app.include_router(create_pulsenet_router(_pulsenet_service))

__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
