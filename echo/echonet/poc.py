"""Proof-of-Continuity validation helpers."""

from __future__ import annotations

from typing import Protocol


class ReceiptStore(Protocol):
    def is_known(self, tip: str) -> bool: ...

    def fetch(self, tip: str): ...


class Keyring(Protocol):
    def verify(self, signer: str, message: str, signature: str) -> bool: ...


def accept_chain(receipts: ReceiptStore, keyring: Keyring, new_tip: str) -> bool:
    """Walk a chain backwards verifying signatures until a known anchor."""

    cur = new_tip
    seen = 0
    while cur and not receipts.is_known(cur) and seen < 5000:
        record = receipts.fetch(cur)
        if record is None:
            return False

        prev_hash = getattr(record, "prev_hash", None)
        signer = getattr(record, "signer", "")
        payload_hash = getattr(record, "payload_hash", "")
        action = getattr(record, "action", "")
        timestamp = int(getattr(record, "ts", 0))
        signature = getattr(record, "signature", "")

        if not prev_hash:
            return False

        message = f"{action}|{payload_hash}|{prev_hash}|{timestamp}|{signer}"
        if not keyring.verify(signer, message, signature):
            return False

        cur = prev_hash
        seen += 1

    if cur and not receipts.is_known(cur):
        return False

    return True


__all__ = ["accept_chain"]
