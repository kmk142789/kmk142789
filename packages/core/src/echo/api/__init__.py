"""Echo API application."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from echo.bridge import BridgeSyncService, EchoBridgeAPI
from echo.bridge.router import create_router as create_bridge_router
from echo.echoforge.api import create_router as create_echoforge_router
from echo.echoforge.service import EchoForgeDashboardService
from echo.echoforge.storage import EchoForgeSessionStore
from echo.pulsenet import AtlasAttestationResolver, PulseNetGatewayService
from echo.pulsenet.api import create_router as create_pulsenet_router
from echo.pulsenet.registration import RegistrationStore
from echo.pulsenet.stream import PulseAttestor, PulseHistoryStreamer
from echo.resonance import HarmonicsAI
from echo.evolver import EchoEvolver
from echo_atlas.api import create_router as create_atlas_router
from echo_atlas.service import AtlasService
from pulse_weaver.api import create_router as create_pulse_weaver_router
from pulse_weaver.service import PulseWeaverService

from .routes_echonet import router as echonet_router
from .routes_registry import router as registry_router
from .routes_timeline import router as timeline_router
from .state import dag, receipts, session_heads, set_dag, set_receipts, set_session_heads
from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver import build_pulse_bus, build_watchdog
from echo.pulseweaver.api import create_router as create_pulse_router
from echo.orchestrator.core import OrchestratorCore
from echo.orchestrator.api import create_router as create_orchestrator_router

app = FastAPI(title="Echo")
app.include_router(echonet_router)
app.include_router(registry_router)
app.include_router(timeline_router)

_bridge_api = EchoBridgeAPI(
    github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
    telegram_chat_id=os.getenv("ECHO_BRIDGE_TELEGRAM_CHAT_ID"),
    firebase_collection=os.getenv("ECHO_BRIDGE_FIREBASE_COLLECTION"),
)
_bridge_state_dir = Path.cwd() / "state" / "bridge"
_bridge_state_dir.mkdir(parents=True, exist_ok=True)
_bridge_sync_service = BridgeSyncService.from_environment(
    state_dir=_bridge_state_dir,
    github_repository=_bridge_api.github_repository,
)
app.include_router(create_bridge_router(api=_bridge_api, sync_service=_bridge_sync_service))

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
_pulsenet_stream = PulseHistoryStreamer(Path.cwd() / "pulse_history.json")
_pulsenet_attestor = PulseAttestor(TemporalLedger(state_dir=_pulsenet_state))
_pulsenet_atlas_resolver = AtlasAttestationResolver(Path.cwd(), _atlas_service)
_pulsenet_service = PulseNetGatewayService(
    project_root=Path.cwd(),
    registration_store=_pulsenet_store,
    pulse_streamer=_pulsenet_stream,
    attestor=_pulsenet_attestor,
    atlas_service=_atlas_service,
    resolver_config=_pulsenet_state / "resolver_sources.json",
    atlas_resolver=_pulsenet_atlas_resolver,
)
app.include_router(create_pulsenet_router(_pulsenet_service))

_echoforge_state = Path.cwd() / "state" / "echoforge"
_echoforge_state.mkdir(parents=True, exist_ok=True)
_echoforge_sessions = EchoForgeSessionStore(_echoforge_state / "sessions.sqlite3")
_echoforge_frontend = Path(__file__).resolve().parent.parent / "echoforge" / "frontend" / "index.html"
_echoforge_service = EchoForgeDashboardService(
    project_root=Path.cwd(),
    pulsenet=_pulsenet_service,
    session_store=_echoforge_sessions,
    atlas_resolver=_pulsenet_atlas_resolver,
    frontend_path=_echoforge_frontend,
)
app.include_router(create_echoforge_router(_echoforge_service))

_orchestrator_state = Path.cwd() / "state" / "orchestrator"
_orchestrator_state.mkdir(parents=True, exist_ok=True)
_orchestrator_service = OrchestratorCore(
    state_dir=_orchestrator_state,
    pulsenet=_pulsenet_service,
    evolver=EchoEvolver(),
    resonance_engine=HarmonicsAI(),
    atlas_resolver=_pulsenet_atlas_resolver,
    bridge_service=_bridge_sync_service,
)
app.include_router(create_orchestrator_router(_orchestrator_service))

__all__ = [
    "app",
    "dag",
    "receipts",
    "session_heads",
    "set_dag",
    "set_receipts",
    "set_session_heads",
]
