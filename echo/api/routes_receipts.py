"""Receipts verification routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..receipts import Receipt, default_keyring, verify_receipt

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.post("/verify")
def verify(payload: dict) -> dict:
    receipt = Receipt(**payload)
    ring = default_keyring()
    valid = verify_receipt(receipt, ring)
    return {"valid": bool(valid)}


__all__ = ["router"]
