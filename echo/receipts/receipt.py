"""Verifiable execution receipts."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Protocol


class SigningKey(Protocol):
    pub: str

    def sign(self, message: str) -> str:
        ...


class Keyring(Protocol):
    def verify(self, pub: str, message: str, signature: str) -> bool:
        ...


@dataclass(slots=True)
class Receipt:
    action: str
    payload_hash: str
    prev_hash: str
    ts: float
    signer: str
    signature: str

    def to_dict(self) -> dict:
        return asdict(self)


def _payload_digest(payload: dict) -> str:
    data = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def make_receipt(action: str, payload: dict, prev_hash: str, key: SigningKey) -> Receipt:
    payload_hash = _payload_digest(payload)
    timestamp = int(time.time())
    message = f"{action}|{payload_hash}|{prev_hash}|{timestamp}|{key.pub}"
    signature = key.sign(message)
    return Receipt(
        action=action,
        payload_hash=payload_hash,
        prev_hash=prev_hash,
        ts=float(timestamp),
        signer=key.pub,
        signature=signature,
    )


def verify_receipt(receipt: Receipt, keyring: Keyring) -> bool:
    timestamp = int(receipt.ts)
    message = f"{receipt.action}|{receipt.payload_hash}|{receipt.prev_hash}|{timestamp}|{receipt.signer}"
    return keyring.verify(receipt.signer, message, receipt.signature)


__all__ = ["Receipt", "make_receipt", "verify_receipt"]
