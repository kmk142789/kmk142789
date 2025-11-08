"""FastAPI router exposing Pulse Weaver watchdog and bus."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from starlette import status
from pydantic import BaseModel, ConfigDict, Field

from echo.atlas.temporal_ledger import LedgerEntryInput, TemporalLedger
from echo.pulseweaver.pulse_bus import PulseBus
from echo.pulseweaver.watchdog import SelfHealingWatchdog, WatchdogConfig
from echo.pulseweaver.fabric import (
    ConsensusRoundResult,
    FabricDiagnosticsReport,
    FabricOperations,
    QuorumHealthSnapshot,
)

__all__ = ["create_router"]


class RepairRequest(BaseModel):
    reason: str
    event: Mapping[str, Any] = Field(default_factory=dict)
    dry_run: Optional[bool] = None
    max_attempts: Optional[int] = None
    cooldown_seconds: Optional[int] = None


class RepairResponse(BaseModel):
    succeeded: bool
    proof_path: str | None
    attempts: int


class IngestReceipt(BaseModel):
    repo: str
    ref: str
    proof_id: str
    stored_at: str


class ConsensusRoundRequest(BaseModel):
    """Request payload for triggering a Fabric consensus round."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(description="Topic or reference evaluated during the consensus round")
    initiator: str = Field(default="api", description="Actor initiating the consensus round")
    quorum: int = Field(default=1, ge=0, description="Minimum approvals required to satisfy quorum")
    approvals: list[str] = Field(
        default_factory=list,
        description="Participants approving the proposal",
    )
    rejections: list[str] = Field(
        default_factory=list,
        description="Participants rejecting the proposal",
    )
    abstentions: list[str] = Field(
        default_factory=list,
        description="Participants abstaining from the proposal",
    )


class RateLimiter:
    def __init__(self, *, capacity: int, refill_rate: float) -> None:
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._updated_at = time.monotonic()
        self._lock = threading.Lock()

    def allow(self, amount: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated_at
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._updated_at = now
            if self._tokens >= amount:
                self._tokens -= amount
                return True
            return False


def _default_rate_limiter() -> RateLimiter:
    capacity = int(os.getenv("ECHO_PULSE_INGEST_CAPACITY", "10"))
    refill_rate = float(os.getenv("ECHO_PULSE_INGEST_REFILL", "1"))
    return RateLimiter(capacity=capacity, refill_rate=refill_rate)


def _resolve_fabric_ops(
    fabric_ops: FabricOperations | None,
    ledger: TemporalLedger,
) -> FabricOperations:
    """Return a FabricOperations instance bound to the ledger's state directory."""

    if fabric_ops is not None:
        return fabric_ops

    state_dir = getattr(ledger, "state_dir", None)
    if state_dir is None:
        ledger_path = getattr(ledger, "_ledger_path", None)
        if ledger_path is not None:
            state_dir = Path(ledger_path).parent
        else:
            state_dir = getattr(ledger, "_state_dir", Path("state"))

    return FabricOperations(state_dir)


def create_router(
    watchdog: SelfHealingWatchdog,
    pulse_bus: PulseBus,
    ledger: TemporalLedger,
    *,
    fabric_ops: FabricOperations | None = None,
    rate_limiter: RateLimiter | None = None,
) -> APIRouter:
    router = APIRouter()
    limiter = rate_limiter or _default_rate_limiter()
    fabric = _resolve_fabric_ops(fabric_ops, ledger)

    @router.get("/pulse/health")
    def pulse_health() -> Mapping[str, Any]:  # pragma: no cover - FastAPI handles response serialisation
        return watchdog.status()

    @router.post("/pulse/repair", response_model=RepairResponse)
    def pulse_repair(request: RepairRequest) -> RepairResponse:
        config = WatchdogConfig(
            dry_run_only=request.dry_run or False,
            max_attempts=request.max_attempts or 1,
            cooldown_seconds=request.cooldown_seconds or 0,
        )
        try:
            report = watchdog.run_cycle(request.event, reason=request.reason, config=config)
        except RuntimeError as exc:  # configuration or cooldown issues
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        if report.succeeded:
            ledger.append(
                LedgerEntryInput(
                    actor="watchdog",
                    action="repair-succeeded",
                    ref=request.reason,
                    proof_id=(report.proof_path.name if report.proof_path else report.reason),
                )
            )
        return RepairResponse(
            succeeded=report.succeeded,
            proof_path=str(report.proof_path) if report.proof_path else None,
            attempts=report.attempts,
        )

    @router.post("/pulse/ingest", response_model=IngestReceipt)
    def pulse_ingest(payload: Mapping[str, Any]):
        if not limiter.allow():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limited")
        try:
            envelope = pulse_bus.ingest(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        ledger.append(
            LedgerEntryInput(
                actor=envelope.repo,
                action=f"pulse:{envelope.kind}",
                ref=envelope.ref,
                proof_id=envelope.proof_id,
            )
        )
        stored_at = datetime.now().isoformat()
        return IngestReceipt(
            repo=envelope.repo,
            ref=envelope.ref,
            proof_id=envelope.proof_id,
            stored_at=stored_at,
        )

    @router.get("/ledger/entries")
    def ledger_entries(since: str | None = None, limit: int = 20) -> Mapping[str, Any]:
        since_dt = datetime.fromisoformat(since) if since else None
        entries = [entry.to_dict() for entry in ledger.iter_entries(since=since_dt, limit=limit)]
        return {"entries": entries}

    @router.get("/ledger/graph.svg")
    def ledger_graph_svg(since: str | None = None, limit: int = 20) -> Response:
        since_dt = datetime.fromisoformat(since) if since else None
        svg = ledger.as_svg(since=since_dt, limit=limit)
        return Response(content=svg, media_type="image/svg+xml")

    @router.post(
        "/fabric/consensus",
        response_model=ConsensusRoundResult,
        status_code=status.HTTP_201_CREATED,
    )
    def fabric_consensus(request: ConsensusRoundRequest) -> ConsensusRoundResult:
        if not (request.approvals or request.rejections or request.abstentions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one vote must be supplied",
            )
        return fabric.trigger_consensus_round(
            ledger,
            topic=request.topic,
            initiator=request.initiator,
            quorum=request.quorum,
            approvals=request.approvals,
            rejections=request.rejections,
            abstentions=request.abstentions,
        )

    @router.get("/fabric/quorum", response_model=QuorumHealthSnapshot)
    def fabric_quorum(window: int = Query(10, ge=1)) -> QuorumHealthSnapshot:
        return fabric.quorum_health(window=window)

    @router.get("/fabric/diagnostics", response_model=FabricDiagnosticsReport)
    def fabric_diagnostics(limit: int | None = Query(None, ge=1)) -> FabricDiagnosticsReport:
        return fabric.diagnostics(limit=limit)

    return router
