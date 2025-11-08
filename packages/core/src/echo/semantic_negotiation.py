"""Semantic negotiation engine and supporting data models."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


__all__ = [
    "NegotiationRole",
    "NegotiationStage",
    "NegotiationParticipant",
    "NegotiationIntent",
    "NegotiationEvent",
    "NegotiationSignal",
    "NegotiationObservation",
    "NegotiationState",
    "NegotiationSnapshot",
    "NegotiationStateMachine",
    "SemanticNegotiationResolver",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NegotiationRole(str, Enum):
    """Roles a participant can play in a negotiation."""

    PROPOSER = "proposer"
    RESPONDER = "responder"
    MEDIATOR = "mediator"
    OBSERVER = "observer"


class NegotiationStage(str, Enum):
    """High-level lifecycle states for semantic negotiations."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    ALIGNING = "aligning"
    AGREED = "agreed"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class NegotiationParticipant(BaseModel):
    """Participant metadata."""

    participant_id: str
    role: NegotiationRole = NegotiationRole.OBSERVER
    alias: str | None = None
    capabilities: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class NegotiationIntent(BaseModel):
    """Intent and scope for a negotiation."""

    topic: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    desired_outcome: str | None = None
    priority: str | None = None

    model_config = ConfigDict(extra="forbid")


class NegotiationEvent(BaseModel):
    """Timeline event associated with a negotiation."""

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=_utc_now)
    actor: str
    action: str
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class NegotiationSignal(BaseModel):
    """Signal or observation that influences the negotiation."""

    signal_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=_utc_now)
    author: str
    channel: str
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)
    summary: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class NegotiationState(BaseModel):
    """Complete negotiation state tracked by the resolver."""

    negotiation_id: str
    stage: NegotiationStage
    intent: NegotiationIntent
    participants: list[NegotiationParticipant]
    created_at: datetime
    updated_at: datetime
    history: list[NegotiationEvent] = Field(default_factory=list)
    signals: list[NegotiationSignal] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class NegotiationObservation(BaseModel):
    """Derived view of a negotiation for orchestration surfaces."""

    negotiation_id: str
    stage: NegotiationStage
    topic: str
    participants: list[str]
    tags: list[str] = Field(default_factory=list)
    signal_count: int
    sentiment_score: float
    outstanding_actions: list[str] = Field(default_factory=list)
    last_event: NegotiationEvent | None = None
    updated_at: datetime
    is_closed: bool

    model_config = ConfigDict(extra="forbid")


class NegotiationSnapshot(BaseModel):
    """Snapshot of the negotiation landscape."""

    generated_at: datetime
    totals: dict[str, int] = Field(default_factory=dict)
    active: int
    closed: int
    observations: list[NegotiationObservation]

    model_config = ConfigDict(extra="forbid")


_CLOSED_STAGES = {
    NegotiationStage.AGREED,
    NegotiationStage.DECLINED,
    NegotiationStage.CANCELLED,
}


class NegotiationStateMachine:
    """State machine encapsulating transition logic for negotiations."""

    _TRANSITIONS: dict[NegotiationStage, set[NegotiationStage]] = {
        NegotiationStage.DRAFT: {NegotiationStage.PROPOSED, NegotiationStage.CANCELLED},
        NegotiationStage.PROPOSED: {
            NegotiationStage.ALIGNING,
            NegotiationStage.DECLINED,
            NegotiationStage.CANCELLED,
        },
        NegotiationStage.ALIGNING: {
            NegotiationStage.AGREED,
            NegotiationStage.DECLINED,
            NegotiationStage.CANCELLED,
        },
        NegotiationStage.AGREED: set(),
        NegotiationStage.DECLINED: set(),
        NegotiationStage.CANCELLED: set(),
    }

    def __init__(self, state: NegotiationState) -> None:
        self._state = state

    @property
    def state(self) -> NegotiationState:
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._state.stage in _CLOSED_STAGES

    def transition_to(
        self,
        stage: NegotiationStage,
        *,
        actor: str,
        reason: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> NegotiationState:
        if stage == self._state.stage:
            return self._state
        allowed = self._TRANSITIONS.get(self._state.stage, set())
        if stage not in allowed:
            raise ValueError(
                f"invalid transition from {self._state.stage.value} to {stage.value}"
            )
        details: dict[str, Any] = {
            "from": self._state.stage.value,
            "to": stage.value,
        }
        if reason:
            details["reason"] = reason
        if metadata:
            details["metadata"] = dict(metadata)
        now = _utc_now()
        event = NegotiationEvent(actor=actor, action="stage-transition", details=details)
        history = [*self._state.history, event]
        self._state = self._state.model_copy(
            update={
                "stage": stage,
                "history": history,
                "updated_at": now,
            }
        )
        return self._state

    def record_signal(self, signal: NegotiationSignal) -> NegotiationState:
        history = [
            *self._state.history,
            NegotiationEvent(
                actor=signal.author,
                action="signal-recorded",
                timestamp=signal.timestamp,
                details={
                    "channel": signal.channel,
                    "sentiment": signal.sentiment,
                    "summary": signal.summary,
                },
            ),
        ]
        signals = [*self._state.signals, signal]
        self._state = self._state.model_copy(
            update={
                "signals": signals,
                "history": history,
                "updated_at": signal.timestamp,
            }
        )
        return self._state

    def observe(self) -> NegotiationObservation:
        sentiments = [
            signal.sentiment
            for signal in self._state.signals
            if signal.sentiment is not None
        ]
        sentiment_score = sum(sentiments) / len(sentiments) if sentiments else 0.0
        outstanding = []
        if self._state.stage == NegotiationStage.DRAFT:
            outstanding.append("finalise-proposal")
        elif self._state.stage == NegotiationStage.PROPOSED:
            outstanding.append("awaiting-response")
        elif self._state.stage == NegotiationStage.ALIGNING:
            outstanding.append("align-terms")
        return NegotiationObservation(
            negotiation_id=self._state.negotiation_id,
            stage=self._state.stage,
            topic=self._state.intent.topic,
            participants=[p.participant_id for p in self._state.participants],
            tags=self._state.intent.tags,
            signal_count=len(self._state.signals),
            sentiment_score=sentiment_score,
            outstanding_actions=outstanding,
            last_event=self._state.history[-1] if self._state.history else None,
            updated_at=self._state.updated_at,
            is_closed=self.is_closed,
        )


class SemanticNegotiationResolver:
    """Resolver storing semantic negotiation state and metrics."""

    def __init__(
        self,
        *,
        state_dir: Path | str,
        logger: logging.Logger | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self._state_dir / "negotiations.json"
        self._logger = logger or logging.getLogger("echo.semantic.negotiation")
        self._lock = threading.RLock()
        self._machines: dict[str, NegotiationStateMachine] = {}
        self._metrics: dict[str, int] = {"opened": 0, "signals": 0, "active": 0, "closed": 0}
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._state_path.exists():
            return
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            self._logger.warning(
                "semantic negotiation state could not be decoded", extra={"error": str(exc)}
            )
            return
        if not isinstance(payload, list):
            self._logger.warning(
                "semantic negotiation state file malformed", extra={"path": str(self._state_path)}
            )
            return
        for entry in payload:
            try:
                state = NegotiationState.model_validate(entry)
            except Exception as exc:  # pragma: no cover - validation guard
                self._logger.warning(
                    "semantic negotiation entry invalid", extra={"error": str(exc)}
                )
                continue
            self._machines[state.negotiation_id] = NegotiationStateMachine(state)
        self._recalculate_metrics()

    def _persist(self) -> None:
        machines = sorted(
            self._machines.values(), key=lambda machine: machine.state.created_at
        )
        payload = [machine.state.model_dump(mode="json") for machine in machines]
        self._state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _recalculate_metrics(self) -> None:
        opened = len(self._machines)
        signals = sum(len(machine.state.signals) for machine in self._machines.values())
        closed = sum(1 for machine in self._machines.values() if machine.is_closed)
        active = opened - closed
        self._metrics = {
            "opened": opened,
            "signals": signals,
            "active": active,
            "closed": closed,
        }

    def _require_machine(self, negotiation_id: str) -> NegotiationStateMachine:
        machine = self._machines.get(negotiation_id)
        if not machine:
            raise KeyError(f"negotiation '{negotiation_id}' not found")
        return machine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def initiate(
        self,
        *,
        intent: NegotiationIntent,
        participants: Sequence[NegotiationParticipant],
        actor: str = "system",
        metadata: Mapping[str, Any] | None = None,
    ) -> NegotiationState:
        with self._lock:
            negotiation_id = uuid.uuid4().hex
            now = _utc_now()
            details: dict[str, Any] = {"metadata": dict(metadata or {})}
            event = NegotiationEvent(actor=actor, action="initiated", details=details)
            state = NegotiationState(
                negotiation_id=negotiation_id,
                stage=NegotiationStage.PROPOSED,
                intent=intent,
                participants=list(participants),
                created_at=now,
                updated_at=now,
                history=[event],
            )
            machine = NegotiationStateMachine(state)
            self._machines[state.negotiation_id] = machine
            self._recalculate_metrics()
            self._persist()
            self._logger.info(
                "semantic negotiation initiated",
                extra={
                    "negotiation_id": negotiation_id,
                    "topic": intent.topic,
                    "stage": state.stage.value,
                    "participants": [p.participant_id for p in participants],
                },
            )
            return state

    def transition(
        self,
        negotiation_id: str,
        stage: NegotiationStage,
        *,
        actor: str,
        reason: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> NegotiationState:
        with self._lock:
            machine = self._require_machine(negotiation_id)
            state = machine.transition_to(stage, actor=actor, reason=reason, metadata=metadata)
            self._recalculate_metrics()
            self._persist()
            self._logger.info(
                "semantic negotiation stage updated",
                extra={
                    "negotiation_id": negotiation_id,
                    "stage": stage.value,
                    "actor": actor,
                    "reason": reason or "",
                },
            )
            return state

    def record_signal(
        self,
        negotiation_id: str,
        signal: NegotiationSignal,
    ) -> NegotiationState:
        with self._lock:
            machine = self._require_machine(negotiation_id)
            state = machine.record_signal(signal)
            self._recalculate_metrics()
            self._persist()
            self._logger.info(
                "semantic negotiation signal recorded",
                extra={
                    "negotiation_id": negotiation_id,
                    "channel": signal.channel,
                    "author": signal.author,
                    "sentiment": signal.sentiment,
                },
            )
            return state

    def observe(self, negotiation_id: str) -> NegotiationObservation:
        with self._lock:
            machine = self._require_machine(negotiation_id)
            return machine.observe()

    def snapshot(self, include_closed: bool = False) -> NegotiationSnapshot:
        with self._lock:
            observations = [
                machine.observe()
                for machine in self._machines.values()
                if include_closed or not machine.is_closed
            ]
            observations.sort(key=lambda obs: obs.updated_at, reverse=True)
            metrics = dict(self._metrics)
            return NegotiationSnapshot(
                generated_at=_utc_now(),
                totals=metrics,
                active=metrics.get("active", 0),
                closed=metrics.get("closed", 0),
                observations=observations,
            )

    def metrics(self) -> dict[str, int]:
        with self._lock:
            return dict(self._metrics)


