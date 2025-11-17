"""Pydantic models for the public Echo Bridge API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConnectorDescriptor(BaseModel):
    """Describe a relay connector that Echo can operate."""

    platform: str = Field(..., description="Target platform for the relay.")
    action: str = Field(..., description="Action performed on the destination platform.")
    requires_secrets: List[str] = Field(
        default_factory=list,
        description="List of secret identifiers required to activate the connector.",
    )


class PlanRequest(BaseModel):
    """Incoming request describing a relay planning scenario."""

    identity: str = Field(..., min_length=1, description="Canonical Echo identity label.")
    cycle: str = Field(..., min_length=1, description="Cycle identifier or tag for the relay.")
    signature: str = Field(..., min_length=1, description="Deterministic signature binding the relay to Echo.")
    traits: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional trait metadata propagated to downstream connectors.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Optional human-readable synopsis appended to bridge payloads.",
    )
    links: Optional[List[str]] = Field(
        default=None,
        description="Optional list of reference links shared with each connector.",
    )


class PlanModel(BaseModel):
    """Materialised representation of a bridge plan."""

    platform: str
    action: str
    payload: Dict[str, Any]
    requires_secret: List[str]

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }


class PlanResponse(BaseModel):
    """Response payload containing a list of plans."""

    plans: List[PlanModel] = Field(..., description="Plans produced for the requested relay.")


class StatusResponse(BaseModel):
    """Expose bridge capabilities and discovery information."""

    connectors: List[ConnectorDescriptor] = Field(
        ..., description="Connectors that are currently configured."
    )


class SyncLogEntry(BaseModel):
    """Structured representation of a bridge sync operation."""

    id: str = Field(..., description="Unique identifier for the sync entry.")
    timestamp: str = Field(..., description="Timestamp for when the sync was recorded.")
    connector: str = Field(..., description="Connector that produced the sync payload.")
    action: str = Field(..., description="Action executed or planned for the connector.")
    status: str = Field(..., description="Outcome status for the sync operation.")
    detail: Optional[str] = Field(
        default=None, description="Human-readable description of the sync operation."
    )
    cycle: Optional[str] = Field(
        default=None, description="Cycle identifier associated with the sync entry."
    )
    coherence: Optional[float] = Field(
        default=None, description="Coherence score at the time of the sync."
    )
    manifest_path: Optional[str] = Field(
        default=None,
        description="Path to the manifest that produced this sync entry, when available.",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured payload forwarded to the downstream connector.",
    )


class SyncResponse(BaseModel):
    """API response bundling sync history entries."""

    cycle: Optional[str] = Field(
        default=None,
        description="Cycle identifier for the latest sync entry contained in the response.",
    )
    operations: List[SyncLogEntry] = Field(
        default_factory=list,
        description="Ordered list of sync operations, newest entries last.",
    )

