"""Telemetry schema definitions with privacy-preserving defaults."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

SENSITIVE_FIELD_MARKERS = {"email", "password", "secret", "token", "name"}


def _normalize_timestamp(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ConsentState(str, Enum):
    """Possible telemetry consent states."""

    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    UNKNOWN = "unknown"

    @property
    def allows_collection(self) -> bool:
        return self is ConsentState.OPTED_IN


class TelemetryContext(BaseModel):
    """Context associated with telemetry events."""

    pseudonymous_id: str = Field(..., alias="id")
    consent_state: ConsentState = Field(default=ConsentState.UNKNOWN)
    consent_recorded_at: Optional[datetime] = None
    session_label: Optional[str] = None

    @field_validator("pseudonymous_id")
    @classmethod
    def _validate_identifier(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError("pseudonymous_id must be non-empty")
        if len(value) < 16:
            raise ValueError("pseudonymous_id must be at least 16 characters for anonymity")
        return value

    @field_validator("consent_recorded_at")
    @classmethod
    def _normalize_consent_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        return _normalize_timestamp(value)

    @classmethod
    def pseudonymize(
        cls,
        *,
        raw_identifier: str,
        salt: str,
        consent_state: ConsentState,
        consent_recorded_at: Optional[datetime] = None,
        session_label: Optional[str] = None,
    ) -> "TelemetryContext":
        """Create a context by hashing the identifier with the provided salt."""

        if not raw_identifier:
            raise ValueError("raw_identifier must be provided for pseudonymisation")
        digest = sha256()
        digest.update(salt.encode("utf-8"))
        digest.update(raw_identifier.encode("utf-8"))
        pseudonymous_id = digest.hexdigest()
        return cls(
            id=pseudonymous_id,
            consent_state=consent_state,
            consent_recorded_at=consent_recorded_at,
            session_label=session_label,
        )


class TelemetryEvent(BaseModel):
    """A telemetry event emitted by the ethical telemetry layer."""

    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context: TelemetryContext
    payload: Mapping[str, Any] = Field(default_factory=dict)
    consent_snapshot: ConsentState | None = None

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError("event_type must be non-empty")
        return value

    @field_validator("occurred_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value) or datetime.now(timezone.utc)

    @field_validator("payload")
    @classmethod
    def _validate_payload(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        for key in value:
            lowered = key.lower()
            if any(marker in lowered for marker in SENSITIVE_FIELD_MARKERS):
                raise ValueError(
                    "payload keys must not include direct identifiers such as names, emails, or secrets"
                )
        return dict(value)

    @model_validator(mode="after")
    def _attach_consent_snapshot(self) -> "TelemetryEvent":
        if self.consent_snapshot is None:
            object.__setattr__(self, "consent_snapshot", self.context.consent_state)
        return self

    def redact(self, allowed_fields: Optional[set[str]] = None) -> "TelemetryEvent":
        """Return a new event containing only safe payload fields."""

        allowed_fields = allowed_fields or set()
        filtered_payload: Dict[str, Any] = {}
        for key, value in self.payload.items():
            if key in allowed_fields:
                filtered_payload[key] = value
        return TelemetryEvent(
            event_type=self.event_type,
            occurred_at=self.occurred_at,
            context=self.context,
            payload=filtered_payload,
            consent_snapshot=self.consent_snapshot,
        )
