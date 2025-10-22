"""Data models for the PulseNet gateway."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, Field, field_validator


class RegistrationRequest(BaseModel):
    """Incoming payload used to register an identity with PulseNet."""

    name: str = Field(..., min_length=1, description="Display name for the registrant")
    contact: str = Field(
        ...,
        min_length=1,
        description="Primary contact channel (email, Matrix handle, etc.)",
    )
    continuum_handle: str | None = Field(
        None, description="Optional handle or key within the Continuum compass"
    )
    unstoppable_domains: list[str] = Field(
        default_factory=list,
        description="Associated Unstoppable Domains entries",
    )
    ens_names: list[str] = Field(
        default_factory=list,
        description="ENS names controlled by the registrant",
    )
    vercel_projects: list[str] = Field(
        default_factory=list,
        description="Relevant Vercel deployments or project slugs",
    )
    wallets: list[str] = Field(
        default_factory=list,
        description="Wallet addresses linked to the identity",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata describing the registrant",
    )

    @field_validator("unstoppable_domains", "ens_names", "vercel_projects", "wallets", mode="before")
    @classmethod
    def _normalise_sequence(cls, value: Any) -> Sequence[str]:  # noqa: D401
        """Ensure optional list-like fields are normalised into lists of strings."""

        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, Sequence):
            raise TypeError("expected a list of strings")
        return [str(item) for item in value]


class RegistrationRecord(BaseModel):
    """Persisted representation of a registration entry."""

    id: str
    name: str
    contact: str
    continuum_handle: str | None = None
    unstoppable_domains: list[str] = Field(default_factory=list)
    ens_names: list[str] = Field(default_factory=list)
    vercel_projects: list[str] = Field(default_factory=list)
    wallets: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["registered_at"] = self.registered_at.isoformat()
        return payload


@dataclass(slots=True)
class PulseHistoryEntry:
    """Single pulse history row derived from ``pulse_history.json``."""

    timestamp: float
    message: str
    hash: str

    @property
    def as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "timestamp": self.timestamp,
            "message": self.message,
            "hash": self.hash,
            "iso": self.as_datetime.isoformat(),
        }


class AttestedPulse(BaseModel):
    """Envelope returned to websocket clients for each pulse."""

    pulse: Mapping[str, Any]
    attestation: Mapping[str, Any]
    summary: Mapping[str, Any]


class ResolutionResult(BaseModel):
    """Payload describing the outcome of a cross-domain resolution query."""

    query: str
    atlas: list[Mapping[str, Any]]
    registrations: list[Mapping[str, Any]]
    domains: Mapping[str, Sequence[str]]


__all__ = [
    "AttestedPulse",
    "PulseHistoryEntry",
    "RegistrationRecord",
    "RegistrationRequest",
    "ResolutionResult",
]
