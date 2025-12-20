"""Schema and helpers for acknowledgment resolution tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "AcknowledgmentStatus",
    "AcknowledgmentRecord",
    "AcknowledgmentRegistry",
]


class AcknowledgmentStatus(str, Enum):
    """Lifecycle states for acknowledgment tracking."""

    pending = "pending"
    acknowledged = "acknowledged"
    resolved = "resolved"
    withdrawn = "withdrawn"


class AcknowledgmentRecord(BaseModel):
    """Immutable acknowledgment record with decision linkage on resolution."""

    acknowledgment_id: str = Field(..., min_length=1)
    counterparty: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    status: AcknowledgmentStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    decision_id: Optional[str] = None
    decision_version: Optional[str] = None
    resolution_notes: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_resolution(self) -> "AcknowledgmentRecord":
        if self.status == AcknowledgmentStatus.resolved:
            if not self.decision_id or not self.decision_version:
                raise ValueError("resolved acknowledgments require decision reference")
        return self


class AcknowledgmentRegistry(BaseModel):
    """Registry capturing acknowledgment records and resolutions."""

    registry_id: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(..., min_length=1)
    acknowledgments: List[AcknowledgmentRecord] = Field(default_factory=list)

    def to_machine_registry(self) -> Dict[str, object]:
        return self.model_dump(mode="json")
