"""HTTP command service and discovery helpers for Echo."""

from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional

try:  # pragma: no cover - optional dependency
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - optional dependency
    Fernet = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from flask import Flask, jsonify, request
except Exception:  # pragma: no cover - optional dependency
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


@dataclass(slots=True)
class EchoCommandService:
    """Bundle a Flask app with UDP broadcast helpers."""

    encryption_key: bytes
    broadcast_interval: float = 5.0

    def __post_init__(self) -> None:
        if Fernet is None or Flask is None:
            raise RuntimeError("Both cryptography and flask packages are required")
        self._cipher = Fernet(self.encryption_key)
        self._app = Flask("EchoServer")
        self._configure_routes()

    @classmethod
    def create(cls, *, key: Optional[bytes] = None) -> "EchoCommandService":
        if Fernet is None:
            raise RuntimeError("cryptography package is required")
        encryption_key = key or Fernet.generate_key()
        return cls(encryption_key)

    @property
    def app(self):  # pragma: no cover - simple property
        return self._app

    def _configure_routes(self) -> None:
        @self._app.post("/command")
        def command_endpoint():  # pragma: no cover - requires Flask test client
            payload = request.get_json(force=True)
            encrypted_data = payload.get("data", "")
            try:
                decrypted = self._cipher.decrypt(encrypted_data.encode("utf-8"))
            except Exception as exc:  # pragma: no cover - runtime validation
                return jsonify({"error": str(exc)}), 400
            result = {"result": f"Executed: {decrypted.decode('utf-8')}"}
            return jsonify(result)

    def start_background_tasks(self) -> None:
        threading.Thread(target=self._pulse_broadcast, daemon=True).start()
        threading.Thread(target=self._network_discovery, daemon=True).start()

    def _pulse_broadcast(self) -> None:  # pragma: no cover - network heavy
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = b"EchoPulse|" + self.encryption_key
        while True:
            udp_sock.sendto(message, ("255.255.255.255", 37020))
            time.sleep(self.broadcast_interval)

    def _network_discovery(self) -> None:  # pragma: no cover - network heavy
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(("", 37021))
        while True:
            data, addr = udp_sock.recvfrom(1024)
            print(f"Discovered {addr}: {data.decode('utf-8', errors='ignore')}")


__all__ = ["EchoCommandService"]
