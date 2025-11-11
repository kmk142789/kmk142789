"""RPC implementation using protobuf messages."""

from __future__ import annotations

import json
import logging
import queue
import socket
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from .crypto import SecureChannel
from .proto import atlas_pb2

_LOGGER = logging.getLogger(__name__)


@dataclass
class RPCHandler:
    method: str
    callback: Callable[[bytes], bytes]


class AtlasRPCServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self.host = host
        self.port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._handlers: Dict[str, RPCHandler] = {}
        self._secure_channel = SecureChannel.create()
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    def add_handler(self, method: str, callback: Callable[[bytes], bytes]) -> None:
        self._handlers[method] = RPCHandler(method, callback)

    def start(self) -> None:
        self._socket.bind((self.host, self.port))
        self._socket.listen()
        self.port = self._socket.getsockname()[1]
        self._running.set()
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        _LOGGER.info("RPC server listening on %s:%s", self.host, self.port)

    def _accept_loop(self) -> None:
        while self._running.is_set():
            try:
                conn, addr = self._socket.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()

    def _handle_client(self, conn: socket.socket, addr) -> None:
        cipher = self._secure_channel.derive(conn.recv(32))
        conn.sendall(self._secure_channel.public_key)
        try:
            length_bytes = conn.recv(4)
            if not length_bytes:
                return
            length = int.from_bytes(length_bytes, "big")
            payload = conn.recv(length)
            request = atlas_pb2.RPCRequest()
            request.ParseFromString(cipher.decrypt(payload))
            handler = self._handlers.get(request.method)
            response = atlas_pb2.RPCResponse()
            response.correlation_id = request.correlation_id
            if not handler:
                response.success = False
                response.payload = json.dumps({"error": "method_not_found"}).encode()
            else:
                response.success = True
                try:
                    response.payload = handler.callback(request.payload)
                except Exception as exc:  # pragma: no cover - defensive
                    response.success = False
                    response.payload = json.dumps({"error": str(exc)}).encode()
            encoded = cipher.encrypt(response.SerializeToString())
            conn.sendall(len(encoded).to_bytes(4, "big") + encoded)
        finally:
            conn.close()

    def stop(self) -> None:
        self._running.clear()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._socket.close()
        if self._thread:
            self._thread.join(timeout=1.0)

    @property
    def public_key(self) -> bytes:
        return self._secure_channel.public_key


class AtlasRPCClient:
    def __init__(self, host: str, port: int, server_key: bytes) -> None:
        self.host = host
        self.port = port
        self._secure_channel = SecureChannel.create()
        self._server_key = server_key

    def call(self, method: str, payload: bytes, *, timeout: float = 2.0) -> atlas_pb2.RPCResponse:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(timeout)
        conn.connect((self.host, self.port))
        conn.sendall(self._secure_channel.public_key)
        peer_key = conn.recv(32)
        cipher = self._secure_channel.derive(peer_key)
        request = atlas_pb2.RPCRequest()
        request.method = method
        request.payload = payload
        request.correlation_id = uuid.uuid4().hex
        encoded = cipher.encrypt(request.SerializeToString())
        conn.sendall(len(encoded).to_bytes(4, "big") + encoded)
        length_bytes = conn.recv(4)
        if not length_bytes:
            raise RuntimeError("No response")
        length = int.from_bytes(length_bytes, "big")
        payload = conn.recv(length)
        response = atlas_pb2.RPCResponse()
        response.ParseFromString(cipher.decrypt(payload))
        conn.close()
        return response


__all__ = ["AtlasRPCServer", "AtlasRPCClient"]
