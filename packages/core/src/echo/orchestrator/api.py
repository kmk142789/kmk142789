"""FastAPI router exposing the orchestrator flow dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .core import OrchestratorCore


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

    return router


__all__ = ["create_router"]
