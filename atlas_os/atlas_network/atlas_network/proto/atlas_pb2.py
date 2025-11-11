"""Lightweight message definitions for Atlas networking."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass


def _encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


@dataclass
class _BaseMessage:
    def SerializeToString(self) -> bytes:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, bytes):
                payload[key] = {"__bytes__": _encode_bytes(value)}
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf8")

    def ParseFromString(self, data: bytes) -> None:
        payload = json.loads(data.decode("utf8"))
        for key, value in payload.items():
            if isinstance(value, dict) and "__bytes__" in value:
                setattr(self, key, _decode_bytes(value["__bytes__"]))
            else:
                setattr(self, key, value)


@dataclass
class RPCRequest(_BaseMessage):
    method: str = ""
    payload: bytes = b""
    correlation_id: str = ""


@dataclass
class RPCResponse(_BaseMessage):
    success: bool = False
    payload: bytes = b""
    correlation_id: str = ""


@dataclass
class NodeAnnouncement(_BaseMessage):
    node_id: str = ""
    host: str = ""
    port: int = 0


@dataclass
class Heartbeat(_BaseMessage):
    node_id: str = ""
    timestamp: int = 0


__all__ = [
    "RPCRequest",
    "RPCResponse",
    "NodeAnnouncement",
    "Heartbeat",
]
