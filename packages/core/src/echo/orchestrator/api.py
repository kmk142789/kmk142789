"""FastAPI router exposing the orchestrator flow dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .core import OrchestratorCore
from .singularity_core import SingularityCore


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


def create_singularity_router(core: SingularityCore) -> APIRouter:
    """Expose Singularity Core decisions over a FastAPI router."""

    router = APIRouter(prefix="/singularity", tags=["singularity"])

    def _get_core() -> SingularityCore:
        return core

    @router.get("/status")
    def status(_: SingularityCore = Depends(_get_core)) -> dict:
        """Return the current singularity status snapshot."""

        return {
            "cycle": core.cycle,
            "universes": list(core.universes),
            "latest_decision": core.latest_decision,
            "prime_artifacts": list(core.prime_artifacts),
        }

    @router.get("/log")
    def log(_: SingularityCore = Depends(_get_core)) -> dict:
        """Return the singularity decision log."""

        return {"log": list(core.singularity_log)}

    return router


__all__ = ["create_router", "create_singularity_router"]
