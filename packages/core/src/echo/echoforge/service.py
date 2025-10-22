"""EchoForge dashboard orchestration layer."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Mapping

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from echo.pulsenet import PulseNetGatewayService

from .storage import EchoForgeSessionStore
from ..pulsenet.atlas import AtlasAttestationResolver


class EchoForgeDashboardService:
    """Coordinate PulseNet streaming, Atlas metadata, and persistence."""

    def __init__(
        self,
        *,
        project_root: Path,
        pulsenet: PulseNetGatewayService,
        session_store: EchoForgeSessionStore,
        atlas_resolver: AtlasAttestationResolver | None = None,
        frontend_path: Path | None = None,
    ) -> None:
        self._project_root = Path(project_root)
        self._pulsenet = pulsenet
        self._session_store = session_store
        self._atlas_resolver = atlas_resolver
        self._frontend_path = frontend_path

    # ------------------------------------------------------------------
    # FastAPI helpers
    # ------------------------------------------------------------------
    async def websocket_stream(self, websocket: WebSocket) -> None:
        session_id = uuid.uuid4().hex
        client = websocket.client
        user_agent = websocket.headers.get("user-agent")
        self._session_store.create_session(
            session_id=session_id,
            client_host=getattr(client, "host", None),
            client_port=getattr(client, "port", None),
            user_agent=user_agent,
        )
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "session",
                "session_id": session_id,
                "summary": self._pulsenet.pulse_summary(),
                "atlas": self._atlas_snapshot(),
                "recent": self._session_store.recent_pulses(limit=25),
            }
        )
        try:
            async for event in self._pulsenet.iter_pulses():
                payload = self._build_event_payload(event)
                self._session_store.store_pulse(session_id, event_payload=payload)
                await websocket.send_json(
                    {
                        "type": "pulse",
                        "session_id": session_id,
                        **payload,
                    }
                )
        except WebSocketDisconnect:  # pragma: no cover - connection lifecycle managed by FastAPI
            return
        except asyncio.CancelledError:  # pragma: no cover - underlying transport closed
            return

    def render_dashboard(self) -> HTMLResponse:
        if not self._frontend_path:
            raise RuntimeError("EchoForge frontend not configured")
        html = self._frontend_path.read_text(encoding="utf-8")
        return HTMLResponse(html)

    def list_sessions(self, *, limit: int = 50) -> list[Mapping[str, object | None]]:
        return [session.as_dict() for session in self._session_store.sessions(limit=limit)]

    def session_payload(self, session_id: str, *, limit: int = 500) -> Mapping[str, object]:
        return self._session_store.session_payload(session_id, limit=limit)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_event_payload(self, event: Mapping[str, object]) -> Mapping[str, object]:
        pulse = event["pulse"]
        attestation = event.get("attestation")
        atlas_payload = event.get("atlas")
        if not atlas_payload and self._atlas_resolver:
            atlas_payload = self._atlas_resolver.lookup(attestation.get("proof_id") if isinstance(attestation, Mapping) else None)
            atlas_payload = atlas_payload.as_dict() if atlas_payload else None
        return {
            "pulse": pulse,
            "attestation": attestation,
            "summary": event.get("summary"),
            "atlas": atlas_payload,
        }

    def _atlas_snapshot(self) -> Mapping[str, object]:
        if not self._atlas_resolver:
            return {"wallets": []}
        return {"wallets": self._atlas_resolver.wallets()}


__all__ = ["EchoForgeDashboardService"]
