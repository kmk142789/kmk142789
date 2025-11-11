"""Heartbeat monitoring with failure detection."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Dict

from .proto import atlas_pb2

_LOGGER = logging.getLogger(__name__)


class HeartbeatMonitor:
    def __init__(self, node_id: str, *, timeout: float = 2.0) -> None:
        self.node_id = node_id
        self.timeout = timeout
        self._listeners: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[str], None]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watchdog, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)

    def register_failure_callback(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    def ingest(self, payload: bytes) -> None:
        heartbeat = atlas_pb2.Heartbeat()
        heartbeat.ParseFromString(payload)
        with self._lock:
            self._listeners[heartbeat.node_id] = heartbeat.timestamp

    def emit(self) -> bytes:
        heartbeat = atlas_pb2.Heartbeat()
        heartbeat.node_id = self.node_id
        heartbeat.timestamp = int(time.time() * 1000)
        return heartbeat.SerializeToString()

    def _watchdog(self) -> None:
        while not self._stop.is_set():
            now = int(time.time() * 1000)
            expired = []
            with self._lock:
                for node_id, timestamp in list(self._listeners.items()):
                    if now - timestamp > self.timeout * 1000:
                        expired.append(node_id)
                        del self._listeners[node_id]
            for node_id in expired:
                _LOGGER.warning("Node %s failed heartbeat", node_id)
                for cb in self._callbacks:
                    cb(node_id)
            time.sleep(self.timeout / 2)


__all__ = ["HeartbeatMonitor"]
