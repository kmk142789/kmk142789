"""FastAPI router exposing the PulseNet gateway."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket

from .models import RegistrationRequest
from .service import PulseNetGatewayService


def create_router(service: PulseNetGatewayService) -> APIRouter:
    router = APIRouter(prefix="/pulsenet", tags=["PulseNet Gateway"])

    @router.post("/register", name="pulsenet_register")
    def _register(payload: RegistrationRequest, gateway: PulseNetGatewayService = Depends(lambda: service)) -> dict:
        record = gateway.register(payload)
        return record

    @router.get("/registrations", name="pulsenet_registrations")
    def _registrations(gateway: PulseNetGatewayService = Depends(lambda: service)) -> list[dict]:
        return gateway.registrations()

    @router.get("/resolve", name="pulsenet_resolve")
    def _resolve(
        identifier: str = Query(..., min_length=1, description="Name, domain, or wallet to resolve"),
        gateway: PulseNetGatewayService = Depends(lambda: service),
    ) -> dict:
        return gateway.resolve(identifier)

    @router.get("/attestations", name="pulsenet_attestations")
    def _attestations(
        limit: int = Query(10, ge=1, le=100, description="Maximum number of attestations to return"),
        gateway: PulseNetGatewayService = Depends(lambda: service),
    ) -> list[dict]:
        return gateway.latest_attestations(limit=limit)

    @router.get("/summary", name="pulsenet_summary")
    def _summary(gateway: PulseNetGatewayService = Depends(lambda: service)) -> dict:
        return gateway.pulse_summary()

    @router.websocket("/pulse-stream")
    async def _pulse_stream(websocket: WebSocket) -> None:
        await service.stream_pulses(websocket)

    return router


__all__ = ["create_router"]
