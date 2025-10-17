"""Pydantic models for Pulse bus payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["PulseMessage"]


class PulseMessage(BaseModel):
    repo: str = Field(..., description="Repository in owner/name format")
    ref: str = Field(..., description="Git commit SHA or reference")
    kind: Literal["merge", "fix", "doc", "schema"]
    summary: str = Field(..., max_length=200)
    proof_id: str = Field(..., min_length=4)
    timestamp: datetime
    signature: str = Field(..., description="Deterministic secp256k1 signature")
    key_id: str = Field(..., description="Identifier of the signing key")
