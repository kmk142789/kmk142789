"""FastAPI router exposing the EchoForge dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket
from fastapi.responses import HTMLResponse

from .service import EchoForgeDashboardService


def create_router(service: EchoForgeDashboardService) -> APIRouter:
    router = APIRouter(prefix="/echoforge", tags=["EchoForge Dashboard"])

    @router.get("/", response_class=HTMLResponse, name="echoforge_index")
    def _dashboard(app: EchoForgeDashboardService = Depends(lambda: service)) -> HTMLResponse:
        return app.render_dashboard()

    @router.get("/sessions", name="echoforge_sessions")
    def _sessions(
        app: EchoForgeDashboardService = Depends(lambda: service),
        limit: int = Query(50, ge=1, le=500),
    ) -> list[dict[str, object | None]]:
        return [dict(item) for item in app.list_sessions(limit=limit)]

    @router.get("/sessions/{session_id}", name="echoforge_session_detail")
    def _session_detail(
        session_id: str,
        app: EchoForgeDashboardService = Depends(lambda: service),
        limit: int = Query(500, ge=1, le=5000),
    ) -> dict[str, object]:
        payload = app.session_payload(session_id, limit=limit)
        return dict(payload)

    @router.websocket("/ws")
    async def _websocket(websocket: WebSocket) -> None:
        await service.websocket_stream(websocket)

    return router


__all__ = ["create_router"]
