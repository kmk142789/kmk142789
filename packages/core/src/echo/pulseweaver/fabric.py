"""Operational helpers for managing the Fabric consensus state."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, MutableMapping, Sequence

from pydantic import BaseModel, Field, ValidationError, field_serializer

from echo.atlas.temporal_ledger import LedgerEntry, LedgerEntryInput, TemporalLedger

__all__ = [
    "ConsensusRoundResult",
    "FabricDiagnosticsReport",
    "FabricOperations",
    "FabricRoundRecord",
    "FabricStatus",
    "QuorumHealthSnapshot",
]

FabricStatus = Literal["stable", "attention", "critical"]


class IsoDatetimeModel(BaseModel):
    """Base model that serialises datetime fields to ISO-8601 for JSON payloads."""

    @field_serializer("*", when_used="json")
    def _serialise_datetime_fields(self, value: Any) -> Any:  # pragma: no cover - thin utility
        return value.isoformat() if isinstance(value, datetime) else value


class FabricRoundRecord(IsoDatetimeModel):
    """Snapshot of a consensus round tracked by the Fabric subsystem."""

    round_id: str = Field(description="Unique identifier generated for the consensus round")
    topic: str = Field(description="Topic or reference that the round evaluated")
    initiator: str = Field(description="Actor responsible for initiating the round")
    quorum: int = Field(ge=0, description="Minimum number of approvals required to satisfy quorum")
    approvals: list[str] = Field(default_factory=list, description="Participants that approved the proposal")
    rejections: list[str] = Field(default_factory=list, description="Participants that rejected the proposal")
    abstentions: list[str] = Field(default_factory=list, description="Participants that abstained from voting")
    consensus: float = Field(ge=0.0, le=1.0, description="Ratio of approvals relative to total recorded votes")
    quorum_met: bool = Field(description="Indicates whether quorum requirements were satisfied")
    status: FabricStatus = Field(description="Derived health classification for the round outcome")
    recorded_at: datetime = Field(description="Timestamp when the round was recorded")
    votes: Mapping[str, str] = Field(
        default_factory=dict,
        description="Raw mapping of participant identifiers to their submitted vote",
    )


class LedgerEntrySummary(IsoDatetimeModel):
    """Slim representation of a ledger entry that recorded a Fabric event."""

    id: str
    ts: datetime
    actor: str
    action: str
    ref: str
    proof_id: str
    hash: str


class ConsensusRoundResult(IsoDatetimeModel):
    """Payload returned when a new consensus round is triggered."""

    round: FabricRoundRecord
    ledger_entry: LedgerEntrySummary


class QuorumHealthSnapshot(IsoDatetimeModel):
    """Rolling health indicator for recent Fabric consensus activity."""

    window: int = Field(description="Number of recent rounds analysed when computing the snapshot")
    total_rounds: int = Field(description="Total number of rounds considered in the snapshot window")
    quorum_met: int = Field(description="Count of rounds that satisfied quorum within the window")
    quorum_failed: int = Field(description="Count of rounds that failed to satisfy quorum within the window")
    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of considered rounds that satisfied quorum",
    )
    average_consensus: float = Field(
        ge=0.0,
        le=1.0,
        description="Average consensus ratio across the analysed rounds",
    )
    status: FabricStatus = Field(description="Heuristic status derived from the average consensus score")
    latest_round: FabricRoundRecord | None = Field(
        default=None,
        description="Most recent round included in the snapshot window, if available",
    )


class FabricDiagnosticsReport(IsoDatetimeModel):
    """Aggregated diagnostics for the Fabric subsystem."""

    generated_at: datetime = Field(description="Timestamp indicating when the diagnostics were generated")
    total_rounds: int = Field(description="Total number of rounds recorded on disk")
    quorum_met: int = Field(description="Global count of rounds that satisfied quorum")
    quorum_failed: int = Field(description="Global count of rounds that failed to satisfy quorum")
    average_consensus: float = Field(
        ge=0.0,
        le=1.0,
        description="Average consensus score computed across all recorded rounds",
    )
    status: FabricStatus = Field(description="Overall health classification derived from consensus trends")
    topics: Mapping[str, int] = Field(
        default_factory=dict,
        description="Frequency count of rounds grouped by topic",
    )
    window: int = Field(description="Number of rounds included in the diagnostics payload")
    rounds: Sequence[FabricRoundRecord] = Field(
        default_factory=list,
        description="Ordered subset of recorded rounds returned in the diagnostics payload",
    )


class FabricOperations:
    """Persist consensus rounds and derive quorum diagnostics for Fabric."""

    def __init__(self, state_dir: Path | str = Path("state")) -> None:
        self._state_dir = Path(state_dir)
        self._fabric_dir = self._state_dir / "fabric"
        self._rounds_path = self._fabric_dir / "consensus_rounds.json"
        self._fabric_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def trigger_consensus_round(
        self,
        ledger: TemporalLedger,
        *,
        topic: str,
        initiator: str,
        quorum: int,
        approvals: Sequence[str],
        rejections: Sequence[str],
        abstentions: Sequence[str],
    ) -> ConsensusRoundResult:
        """Record a new consensus round and append an event to the ledger."""

        approvals_list, rejections_list, abstentions_list, votes = self._compose_votes(
            approvals, rejections, abstentions
        )
        total_votes = len(votes)
        consensus_ratio = 0.0 if total_votes == 0 else len(approvals_list) / total_votes
        recorded_at = datetime.now(timezone.utc)
        round_id = recorded_at.strftime("%Y%m%dT%H%M%S%fZ")
        quorum_value = max(0, quorum)
        quorum_met = len(approvals_list) >= quorum_value if total_votes else False
        status = self._status_from_consensus(consensus_ratio if quorum_met else consensus_ratio / 2.0)

        record = FabricRoundRecord(
            round_id=round_id,
            topic=topic,
            initiator=initiator,
            quorum=quorum_value,
            approvals=approvals_list,
            rejections=rejections_list,
            abstentions=abstentions_list,
            consensus=round(consensus_ratio, 4),
            quorum_met=quorum_met,
            status=status,
            recorded_at=recorded_at,
            votes=votes,
        )

        rounds = self._load_rounds()
        rounds.append(record)
        self._persist_rounds(rounds)

        entry = ledger.append(
            LedgerEntryInput(
                actor=initiator,
                action="fabric-consensus",
                ref=topic,
                proof_id=round_id,
            )
        )

        return ConsensusRoundResult(round=record, ledger_entry=self._summarise_entry(entry))

    def quorum_health(self, *, window: int = 10) -> QuorumHealthSnapshot:
        """Compute a rolling quorum health snapshot for recent rounds."""

        rounds = self._load_rounds()
        analysed = rounds[-window:] if window > 0 else rounds
        total = len(analysed)
        quorum_met = sum(1 for record in analysed if record.quorum_met)
        quorum_failed = total - quorum_met
        average_consensus = (
            round(sum(record.consensus for record in analysed) / total, 4) if total else 0.0
        )
        status = self._status_from_consensus(average_consensus)
        success_rate = round(quorum_met / total, 4) if total else 0.0
        latest = analysed[-1] if analysed else None
        return QuorumHealthSnapshot(
            window=window,
            total_rounds=total,
            quorum_met=quorum_met,
            quorum_failed=quorum_failed,
            success_rate=success_rate,
            average_consensus=average_consensus,
            status=status,
            latest_round=latest,
        )

    def diagnostics(self, *, limit: int | None = None) -> FabricDiagnosticsReport:
        """Aggregate Fabric diagnostics including topic and quorum statistics."""

        rounds = self._load_rounds()
        window_rounds = rounds[-limit:] if limit else rounds
        total = len(rounds)
        quorum_met = sum(1 for record in rounds if record.quorum_met)
        quorum_failed = total - quorum_met
        average_consensus = round(sum(record.consensus for record in rounds) / total, 4) if total else 0.0
        status = self._status_from_consensus(average_consensus)
        topics = Counter(record.topic for record in rounds)
        generated_at = datetime.now(timezone.utc)
        return FabricDiagnosticsReport(
            generated_at=generated_at,
            total_rounds=total,
            quorum_met=quorum_met,
            quorum_failed=quorum_failed,
            average_consensus=average_consensus,
            status=status,
            topics=dict(topics),
            window=len(window_rounds),
            rounds=window_rounds,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compose_votes(
        self,
        approvals: Sequence[str],
        rejections: Sequence[str],
        abstentions: Sequence[str],
    ) -> tuple[list[str], list[str], list[str], MutableMapping[str, str]]:
        votes: MutableMapping[str, str] = {}
        approvals_list = self._normalise_votes(approvals, votes, "approve")
        rejections_list = self._normalise_votes(rejections, votes, "reject")
        abstentions_list = self._normalise_votes(abstentions, votes, "abstain")
        return approvals_list, rejections_list, abstentions_list, votes

    def _normalise_votes(
        self,
        values: Sequence[str],
        votes: MutableMapping[str, str],
        label: str,
    ) -> list[str]:
        ordered: list[str] = []
        for value in values:
            participant = value.strip()
            if not participant or participant in votes:
                continue
            votes[participant] = label
            ordered.append(participant)
        return ordered

    def _load_rounds(self) -> list[FabricRoundRecord]:
        raw = self._load_state().get("rounds", [])
        records: list[FabricRoundRecord] = []
        for entry in raw:
            if not isinstance(entry, Mapping):
                continue
            try:
                records.append(FabricRoundRecord.model_validate(entry))
            except ValidationError:
                continue
        records.sort(key=lambda record: record.recorded_at)
        return records

    def _persist_rounds(self, rounds: Iterable[FabricRoundRecord]) -> None:
        payload = {
            "rounds": [record.model_dump(mode="json") for record in rounds],
        }
        self._rounds_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _load_state(self) -> Mapping[str, object]:
        if not self._rounds_path.exists():
            return {"rounds": []}
        try:
            return json.loads(self._rounds_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"rounds": []}

    def _summarise_entry(self, entry: LedgerEntry) -> LedgerEntrySummary:
        return LedgerEntrySummary(
            id=entry.id,
            ts=entry.ts,
            actor=entry.actor,
            action=entry.action,
            ref=entry.ref,
            proof_id=entry.proof_id,
            hash=entry.hash,
        )

    def _status_from_consensus(self, consensus: float) -> FabricStatus:
        if consensus >= 0.75:
            return "stable"
        if consensus >= 0.5:
            return "attention"
        return "critical"
