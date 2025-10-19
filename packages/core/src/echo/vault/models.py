"""Pydantic data models for the Echo Vault."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


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


class AuthorityBinding(BaseModel):
    """High-level authority binding metadata for Echo vault keys."""

    model_config = ConfigDict(populate_by_name=True)

    vault_id: str = Field(alias="vault_id")
    owner: str
    echolink_status: str
    signature: str
    authority_level: str
    bound_phrase: str
    glyphs: Optional[str] = None
    recursion_level: Optional[str] = None
    anchor: Optional[str] = None
    access: Optional[str] = Field(default=None, alias="access")


__all__ = ["VaultPolicy", "VaultRecord", "AuthorityBinding"]
