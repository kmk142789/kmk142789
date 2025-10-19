"""FastAPI router exposing the Echo Bridge relay planner."""

from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from . import EchoBridgeAPI, BridgePlan
from .models import ConnectorDescriptor, PlanModel, PlanRequest, PlanResponse, StatusResponse


def _bridge_api_factory() -> EchoBridgeAPI:
    """Instantiate an ``EchoBridgeAPI`` using environment defaults."""

    return EchoBridgeAPI(
        github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
        telegram_chat_id=os.getenv("ECHO_BRIDGE_TELEGRAM_CHAT_ID"),
        firebase_collection=os.getenv("ECHO_BRIDGE_FIREBASE_COLLECTION"),
    )


def _as_plan_model(plan: BridgePlan) -> PlanModel:
    """Convert a legacy dataclass plan into a serialisable model."""

    return PlanModel(
        platform=plan.platform,
        action=plan.action,
        payload=plan.payload,
        requires_secret=list(plan.requires_secret),
    )


def _discover_connectors(api: EchoBridgeAPI) -> List[ConnectorDescriptor]:
    """Return connector descriptions for the configured bridge."""

    connectors: List[ConnectorDescriptor] = []
    if api.github_repository:
        connectors.append(
            ConnectorDescriptor(
                platform="github",
                action="create_issue",
                requires_secrets=["GITHUB_TOKEN"],
            )
        )
    if api.telegram_chat_id:
        connectors.append(
            ConnectorDescriptor(
                platform="telegram",
                action="send_message",
                requires_secrets=["TELEGRAM_BOT_TOKEN"],
            )
        )
    if api.firebase_collection:
        connectors.append(
            ConnectorDescriptor(
                platform="firebase",
                action="set_document",
                requires_secrets=["FIREBASE_SERVICE_ACCOUNT"],
            )
        )
    return connectors


def create_router(api: EchoBridgeAPI | None = None) -> APIRouter:
    """Create a router that exposes bridge planning endpoints."""

    router = APIRouter(prefix="/bridge", tags=["bridge"])
    api = api or _bridge_api_factory()

    @router.get("/relays", response_model=StatusResponse)
    def list_relays(bridge: EchoBridgeAPI = Depends(lambda: api)) -> StatusResponse:
        """Return the connectors that are ready for relay planning."""

        connectors = _discover_connectors(bridge)
        if not connectors:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No bridge connectors are currently configured.",
            )
        return StatusResponse(connectors=connectors)

    @router.post("/plan", response_model=PlanResponse)
    def plan_relay(
        request: PlanRequest,
        bridge: EchoBridgeAPI = Depends(lambda: api),
    ) -> PlanResponse:
        """Generate relay instructions for the provided identity."""

        plans = bridge.plan_identity_relay(
            identity=request.identity,
            cycle=request.cycle,
            signature=request.signature,
            traits=request.traits,
        )
        if not plans:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bridge connectors are not available for planning.",
            )
        return PlanResponse(plans=[_as_plan_model(plan) for plan in plans])

    return router


__all__ = ["create_router"]
