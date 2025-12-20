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
    topics: Optional[List[str]] = Field(
        default=None,
        description="Optional list of topics or hashtags to propagate to social relays.",
        examples=[["Pulse Orbit", "Echo Bridge"]],
    )
    priority: Optional[str] = Field(
        default=None,
        description="Optional priority hint applied to messages and webhook payloads.",
        examples=["info", "high", "critical"],
    )
    connectors: Optional[List[str]] = Field(
        default=None,
        description="Limit planning to the supplied connector names (case-insensitive).",
        examples=[["slack", "webhook"]],
    )
    secret_payload: Optional[str] = Field(
        default=None,
        description=(
            "Optional Base64-encoded secret payload to store privately while "
            "exposing only decoded metadata to bridge connectors."
        ),
    )
    secret_label: Optional[str] = Field(
        default=None,
        description="Optional label describing the secret payload stored privately.",
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
    sync_connectors: Optional[List[ConnectorDescriptor]] = Field(
        default=None,
        description=(
            "Optional list of sync connectors available to the orchestrator. "
            "Included when sync metadata is requested by the caller."
        ),
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


class SyncStats(BaseModel):
    """Aggregated metrics about the sync operations returned by the API."""

    total_operations: int = Field(
        ..., description="Total number of sync operations contained in the response."
    )
    by_connector: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of operations grouped by connector name.",
    )
    cycles: List[str] = Field(
        default_factory=list,
        description="Unique cycles represented in the returned operations, newest last.",
    )


class SyncRequest(BaseModel):
    """Request payload for executing a sync from an orchestrator decision."""

    decision: Dict[str, Any] = Field(
        ..., description="Raw orchestrator decision document to derive sync payloads from."
    )
    connectors: Optional[List[str]] = Field(
        default=None,
        description="Optional connector names to limit the sync run to.",
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
    stats: Optional[SyncStats] = Field(
        default=None,
        description="Optional aggregate metrics about the included sync operations.",
    )
