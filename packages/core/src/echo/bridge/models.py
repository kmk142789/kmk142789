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

