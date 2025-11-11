"""Node discovery service built on UDP multicast."""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable

_LOGGER = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    node_id: str
    host: str
    port: int
    last_seen: float


class NodeDiscoveryService:
    def __init__(
        self,
        node_id: str,
        host: str,
        port: int,
        *,
        group: str = "239.20.20.20",
        ttl: int = 1,
        listen_port: int = 45678,
    ) -> None:
        self.node_id = node_id
        self.host = host
        self.port = port
        self.group = group
        self.ttl = ttl
        self.listen_port = listen_port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._peers: Dict[str, NodeInfo] = {}

    def start(self) -> None:
        self._sock.bind(("", self.listen_port))
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._sock.close()
        self._thread.join(timeout=1.0)

    def announce(self) -> None:
        payload = json.dumps({"node_id": self.node_id, "host": self.host, "port": self.port}).encode()
        self._sock.sendto(payload, (self.group, self.listen_port))

    def _listen_loop(self) -> None:
        while not self._stop.is_set():
            try:
                data, addr = self._sock.recvfrom(1024)
            except OSError:
                break
            self.ingest_announcement(data)

    def peers(self) -> Iterable[NodeInfo]:
        return list(self._peers.values())

    def ingest_announcement(self, payload: bytes) -> None:
        try:
            data = json.loads(payload.decode())
        except json.JSONDecodeError:  # pragma: no cover
            return
        node_id = data.get("node_id")
        if node_id == self.node_id:
            return
        info = NodeInfo(node_id, data.get("host"), int(data.get("port")), time.time())
        self._peers[node_id] = info
        _LOGGER.debug("Discovered node %s at %s", node_id, info.host)


__all__ = ["NodeDiscoveryService", "NodeInfo"]
