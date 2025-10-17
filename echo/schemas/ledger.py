"""Ledger entry schema definitions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

__all__ = ["LedgerEntrySchema"]


class LedgerEntrySchema(BaseModel):
    id: str
    ts: datetime
    actor: str
    action: str
    ref: str
    proof_id: str
    hash: str = Field(..., min_length=64, max_length=64)
