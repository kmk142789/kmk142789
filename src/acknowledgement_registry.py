"""External acknowledgement registry and evidence validation workflow."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class AcknowledgementStatus(str, Enum):
    """Lifecycle states for outbound diplomatic/legal acknowledgements."""

    DRAFTED = "drafted"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"
    VALIDATED = "validated"


STATUS_ORDER = [
    AcknowledgementStatus.DRAFTED,
    AcknowledgementStatus.DISPATCHED,
    AcknowledgementStatus.ACKNOWLEDGED,
    AcknowledgementStatus.VALIDATED,
]


STATUS_REQUIREMENTS: Mapping[AcknowledgementStatus, set[str]] = {
    AcknowledgementStatus.DISPATCHED: {"dispatch_receipt", "courier_tracking"},
    AcknowledgementStatus.ACKNOWLEDGED: {"acknowledgement_letter", "public_statement"},
    AcknowledgementStatus.VALIDATED: {"attestation", "counterparty_signature"},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ScorecardBinding:
    """Links the acknowledgement to a sovereignty scorecard entry."""

    scorecard_path: str
    pillar: str
    scorecard_item: str
    owner: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class EvidenceItem:
    """Proof artifact linked to an acknowledgement."""

    kind: str
    location: str
    collected_at: str
    collector: str
    checksum: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class StatusEntry:
    """Audit trail entry for status transitions."""

    status: str
    recorded_at: str
    actor: str
    rationale: str | None = None


@dataclass
class OutboundArtifact:
    """Represents an outbound diplomatic or legal artifact."""

    title: str
    category: str
    issued_at: str
    counterparty: str
    summary: str
    artifact_path: str
    dispatch_channel: str
    scorecard_binding: ScorecardBinding


@dataclass
class AcknowledgementRecord:
    """Registry entry describing an outbound acknowledgement workflow."""

    record_id: str
    artifact: OutboundArtifact
    status: str = AcknowledgementStatus.DRAFTED.value
    evidence: list[EvidenceItem] = field(default_factory=list)
    status_history: list[StatusEntry] = field(default_factory=list)


class EvidenceValidationError(ValueError):
    """Raised when evidence cannot be validated."""


class StatusAdvancementError(ValueError):
    """Raised when a status transition is not allowed."""


class EvidenceValidator:
    """Validates evidence files and ensures checksums are consistent."""

    def validate(self, evidence: EvidenceItem, base_path: Path | None = None) -> EvidenceItem:
        path = Path(evidence.location)
        resolved = (base_path / path).resolve() if base_path and not path.is_absolute() else path

        if resolved.exists():
            calculated = self._hash_file(resolved)
            if evidence.checksum and evidence.checksum != calculated:
                raise EvidenceValidationError(
                    f"Checksum mismatch for {evidence.location}: {evidence.checksum} != {calculated}"
                )
            if evidence.checksum is None:
                return EvidenceItem(
                    **{**asdict(evidence), "checksum": calculated},
                )
        elif evidence.checksum is None:
            raise EvidenceValidationError(
                f"Evidence at {evidence.location} is missing and no checksum provided."
            )

        return evidence

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return f"sha256:{digest.hexdigest()}"


class ExternalAcknowledgementRegistry:
    """Registry for outbound acknowledgements tied to sovereignty scorecards."""

    def __init__(self, path: Path, validator: EvidenceValidator | None = None) -> None:
        self._path = path
        self._validator = validator or EvidenceValidator()
        self._records: dict[str, AcknowledgementRecord] = {}
        if self._path.exists():
            self._load()

    def register_artifact(self, artifact: OutboundArtifact, actor: str) -> AcknowledgementRecord:
        record_id = uuid.uuid4().hex
        record = AcknowledgementRecord(
            record_id=record_id,
            artifact=artifact,
            status=AcknowledgementStatus.DRAFTED.value,
            status_history=[
                StatusEntry(
                    status=AcknowledgementStatus.DRAFTED.value,
                    recorded_at=_utc_now(),
                    actor=actor,
                    rationale="Initial outbound artifact logged.",
                )
            ],
        )
        self._records[record_id] = record
        self._persist()
        return record

    def add_evidence(
        self, record_id: str, evidence: EvidenceItem, base_path: Path | None = None
    ) -> EvidenceItem:
        record = self._get(record_id)
        validated = self._validator.validate(evidence, base_path=base_path)
        record.evidence.append(validated)
        self._persist()
        return validated

    def advance_status(self, record_id: str, new_status: AcknowledgementStatus, actor: str) -> None:
        record = self._get(record_id)
        current_status = AcknowledgementStatus(record.status)
        if STATUS_ORDER.index(new_status) <= STATUS_ORDER.index(current_status):
            raise StatusAdvancementError(
                f"Cannot move from {current_status.value} to {new_status.value}."
            )

        missing = self._missing_requirements(record, new_status)
        if missing:
            raise StatusAdvancementError(
                f"Missing evidence kinds for {new_status.value}: {', '.join(sorted(missing))}"
            )

        record.status = new_status.value
        record.status_history.append(
            StatusEntry(
                status=new_status.value,
                recorded_at=_utc_now(),
                actor=actor,
                rationale="Evidence requirements satisfied.",
            )
        )
        self._persist()

    def bind_scorecard(self, record_id: str, binding: ScorecardBinding) -> None:
        record = self._get(record_id)
        record.artifact.scorecard_binding = binding
        self._persist()

    def list_records(self) -> Iterable[AcknowledgementRecord]:
        return tuple(self._records.values())

    def get_record(self, record_id: str) -> AcknowledgementRecord:
        return self._get(record_id)

    def _missing_requirements(
        self, record: AcknowledgementRecord, new_status: AcknowledgementStatus
    ) -> set[str]:
        required = STATUS_REQUIREMENTS.get(new_status, set())
        if not required:
            return set()
        available = {item.kind for item in record.evidence}
        if available.intersection(required):
            return set()
        return required

    def _get(self, record_id: str) -> AcknowledgementRecord:
        if record_id not in self._records:
            raise KeyError(f"Record {record_id} not found")
        return self._records[record_id]

    def _load(self) -> None:
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        for entry in payload.get("records", []):
            record = AcknowledgementRecord(
                record_id=entry["record_id"],
                artifact=OutboundArtifact(
                    **{
                        **entry["artifact"],
                        "scorecard_binding": ScorecardBinding(
                            **entry["artifact"]["scorecard_binding"]
                        ),
                    }
                ),
                status=entry["status"],
                evidence=[EvidenceItem(**item) for item in entry.get("evidence", [])],
                status_history=[
                    StatusEntry(**item) for item in entry.get("status_history", [])
                ],
            )
            self._records[record.record_id] = record

    def _persist(self) -> None:
        payload = {
            "updated_at": _utc_now(),
            "records": [self._serialize(record) for record in self._records.values()],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _serialize(record: AcknowledgementRecord) -> dict[str, object]:
        artifact = asdict(record.artifact)
        artifact["scorecard_binding"] = asdict(record.artifact.scorecard_binding)
        return {
            "record_id": record.record_id,
            "artifact": artifact,
            "status": record.status,
            "evidence": [asdict(item) for item in record.evidence],
            "status_history": [asdict(item) for item in record.status_history],
        }


def build_outbound_artifact(
    *,
    title: str,
    category: str,
    counterparty: str,
    summary: str,
    artifact_path: str,
    dispatch_channel: str,
    scorecard_path: str,
    scorecard_pillar: str,
    scorecard_item: str,
    owner: str | None = None,
    notes: str | None = None,
) -> OutboundArtifact:
    """Convenience helper for constructing outbound artifacts."""

    return OutboundArtifact(
        title=title,
        category=category,
        issued_at=_utc_now(),
        counterparty=counterparty,
        summary=summary,
        artifact_path=artifact_path,
        dispatch_channel=dispatch_channel,
        scorecard_binding=ScorecardBinding(
            scorecard_path=scorecard_path,
            pillar=scorecard_pillar,
            scorecard_item=scorecard_item,
            owner=owner,
            notes=notes,
        ),
    )
