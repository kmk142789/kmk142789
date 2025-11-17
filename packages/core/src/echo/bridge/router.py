"""FastAPI router exposing the Echo Bridge relay planner and sync history."""

from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from . import EchoBridgeAPI, BridgePlan
from .models import (
    ConnectorDescriptor,
    PlanModel,
    PlanRequest,
    PlanResponse,
    StatusResponse,
    SyncLogEntry,
    SyncResponse,
)
from .service import BridgeSyncService


def _bridge_api_factory() -> EchoBridgeAPI:
    """Instantiate an ``EchoBridgeAPI`` using environment defaults."""

    return EchoBridgeAPI(
        github_repository=os.getenv("ECHO_BRIDGE_GITHUB_REPOSITORY"),
        telegram_chat_id=os.getenv("ECHO_BRIDGE_TELEGRAM_CHAT_ID"),
        firebase_collection=os.getenv("ECHO_BRIDGE_FIREBASE_COLLECTION"),
        slack_webhook_url=os.getenv("ECHO_BRIDGE_SLACK_WEBHOOK_URL"),
        slack_channel=os.getenv("ECHO_BRIDGE_SLACK_CHANNEL"),
        slack_secret_name=os.getenv("ECHO_BRIDGE_SLACK_SECRET", "SLACK_WEBHOOK_URL"),
        webhook_url=os.getenv("ECHO_BRIDGE_WEBHOOK_URL"),
        webhook_secret_name=os.getenv("ECHO_BRIDGE_WEBHOOK_SECRET", "ECHO_BRIDGE_WEBHOOK_URL"),
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
    if api.slack_webhook_url:
        connectors.append(
            ConnectorDescriptor(
                platform="slack",
                action="send_webhook",
                requires_secrets=[api.slack_secret_name] if api.slack_secret_name else [],
            )
        )
    if api.webhook_url:
        connectors.append(
            ConnectorDescriptor(
                platform="webhook",
                action="post_json",
                requires_secrets=[api.webhook_secret_name] if api.webhook_secret_name else [],
            )
        )
    return connectors


def create_router(
    api: EchoBridgeAPI | None = None,
    sync_service: BridgeSyncService | None = None,
) -> APIRouter:
    """Create a router that exposes bridge planning and sync endpoints."""

    router = APIRouter(prefix="/bridge", tags=["bridge"])
    api = api or _bridge_api_factory()
    sync_service = sync_service or BridgeSyncService.from_environment(
        github_repository=api.github_repository
    )

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
            summary=request.summary,
            links=request.links,
        )
        if not plans:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bridge connectors are not available for planning.",
        )
        return PlanResponse(plans=[_as_plan_model(plan) for plan in plans])

    @router.get("/sync", response_model=SyncResponse)
    def sync_history(
        limit: int = Query(10, ge=1, le=200),
        service: BridgeSyncService = Depends(lambda: sync_service),
    ) -> SyncResponse:
        """Return historical sync operations generated by the orchestrator."""

        entries = service.history(limit=limit)
        latest_cycle = entries[-1].get("cycle") if entries else None
        operations = [SyncLogEntry(**entry) for entry in entries]
        return SyncResponse(cycle=latest_cycle, operations=operations)

    return router


__all__ = ["create_router"]
