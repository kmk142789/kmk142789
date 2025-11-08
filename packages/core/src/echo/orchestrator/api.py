"""FastAPI router exposing the orchestrator flow dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from echo.semantic_negotiation import (
    NegotiationIntent,
    NegotiationParticipant,
    NegotiationStage,
)

from .core import OrchestratorCore


class NegotiationOpenRequest(BaseModel):
    intent: NegotiationIntent
    participants: list[NegotiationParticipant]
    actor: str = Field(default="system", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NegotiationStageRequest(BaseModel):
    stage: NegotiationStage
    actor: str = Field(default="system", min_length=1)
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NegotiationSignalRequest(BaseModel):
    author: str
    channel: str
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)
    summary: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def create_router(orchestrator: OrchestratorCore) -> APIRouter:
    """Return a router exposing the orchestrator flow endpoint."""

    router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

    def _get_service() -> OrchestratorCore:
        return orchestrator

    @router.get("/flow")
    def flow(_: OrchestratorCore = Depends(_get_service)) -> dict:
        """Return the living graph describing active orchestration flows."""

        decision = orchestrator.orchestrate()
        return {
            "timestamp": decision.get("timestamp"),
            "principles": decision.get("principles", []),
            "graph": decision.get("graph", {}),
            "weights": decision.get("weights", {}),
            "coherence": decision.get("coherence", {}),
            "manifest": decision.get("manifest"),
        }

    @router.get("/negotiations")
    def negotiations(
        include_closed: bool = False,
        _: OrchestratorCore = Depends(_get_service),
    ) -> dict:
        """Return the negotiation snapshot managed by the orchestration layer."""

        return orchestrator.negotiation_snapshot(include_closed=include_closed)

    @router.get("/negotiations/metrics")
    def negotiation_metrics(_: OrchestratorCore = Depends(_get_service)) -> dict:
        """Expose aggregate metrics for semantic negotiations."""

        return orchestrator.negotiation_metrics()

    @router.post("/negotiations", status_code=status.HTTP_201_CREATED)
    def open_negotiation(
        request: NegotiationOpenRequest,
        _: OrchestratorCore = Depends(_get_service),
    ) -> dict:
        """Initiate a new semantic negotiation."""

        try:
            return orchestrator.initiate_negotiation(
                request.intent,
                request.participants,
                actor=request.actor,
                metadata=request.metadata,
            )
        except RuntimeError as exc:  # pragma: no cover - propagated to caller
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc

    @router.post("/negotiations/{negotiation_id}/stage")
    def advance_negotiation(
        negotiation_id: str,
        request: NegotiationStageRequest,
        _: OrchestratorCore = Depends(_get_service),
    ) -> dict:
        """Advance the lifecycle stage for an existing negotiation."""

        try:
            return orchestrator.update_negotiation_stage(
                negotiation_id,
                request.stage,
                actor=request.actor,
                reason=request.reason,
                metadata=request.metadata,
            )
        except RuntimeError as exc:  # pragma: no cover - misconfiguration
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="negotiation not found"
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.post(
        "/negotiations/{negotiation_id}/signals",
        status_code=status.HTTP_202_ACCEPTED,
    )
    def register_signal(
        negotiation_id: str,
        request: NegotiationSignalRequest,
        _: OrchestratorCore = Depends(_get_service),
    ) -> dict:
        """Record a new signal for a negotiation."""

        try:
            return orchestrator.record_negotiation_signal(
                negotiation_id,
                author=request.author,
                channel=request.channel,
                sentiment=request.sentiment,
                summary=request.summary,
                payload=request.payload,
            )
        except RuntimeError as exc:  # pragma: no cover - misconfiguration
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="negotiation not found"
            ) from exc

    return router


__all__ = ["create_router"]
