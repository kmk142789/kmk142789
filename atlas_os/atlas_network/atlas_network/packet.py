"""Packet encoding helpers used by the RPC and discovery services."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass(slots=True)
class PacketEnvelope:
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    nonce: str

    def encode(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True).encode("utf8")

    @classmethod
    def decode(cls, data: bytes) -> "PacketEnvelope":
        payload = json.loads(data.decode("utf8"))
        return cls(payload["message_type"], payload["payload"], payload["timestamp"], payload["nonce"])

    @classmethod
    def create(cls, message_type: str, payload: Dict[str, Any], nonce: str) -> "PacketEnvelope":
        return cls(message_type, payload, time.time(), nonce)


__all__ = ["PacketEnvelope"]
