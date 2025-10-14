"""Pydantic data models for the Echo Vault."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class VaultPolicy(BaseModel):
    """Usage guardrails associated with a vault record."""

    max_sign_uses: int = 0
    cooldown_s: int = 0
    allow_formats: List[Literal["hex", "wif"]] = ["hex", "wif"]


class VaultRecord(BaseModel):
    """Metadata describing an encrypted private key entry."""

    id: str
    label: str
    fmt: Literal["hex", "wif"]
    created_at: float
    entropy_hint: str
    policy: VaultPolicy = Field(default_factory=VaultPolicy)
    last_used_at: Optional[float] = None
    use_count: int = 0
    tags: List[str] = Field(default_factory=list)


__all__ = ["VaultPolicy", "VaultRecord"]
