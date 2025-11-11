"""Distributed virtual filesystem orchestrating pluggable drivers."""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Protocol

from .transaction import TransactionLog

_LOGGER = logging.getLogger(__name__)


class FileDriver(Protocol):
    """Protocol implemented by storage drivers."""

    name: str

    def read(self, path: str) -> bytes: ...

    def write(self, path: str, data: bytes) -> None: ...

    def list(self, prefix: str = "") -> Iterable[str]: ...

    def delete(self, path: str) -> None: ...


@dataclass
class StorageNode:
    node_id: str
    driver: FileDriver
    capacity_bytes: int
    metadata: Dict[str, str] = field(default_factory=dict)


class DistributedVirtualFileSystem:
    """Coordinates multiple storage nodes providing a unified namespace."""

    def __init__(self, transaction_log: Optional[TransactionLog] = None) -> None:
        self._nodes: Dict[str, StorageNode] = {}
        self._lock = threading.RLock()
        self._transaction_log = transaction_log or TransactionLog()

    def register_node(self, node: StorageNode) -> None:
        with self._lock:
            self._nodes[node.node_id] = node
            self._transaction_log.append(
                "register_node",
                {
                    "node_id": node.node_id,
                    "driver": node.driver.name,
                    "capacity": node.capacity_bytes,
                },
            )
            _LOGGER.debug("Registered storage node %s", node.node_id)

    def remove_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)
            self._transaction_log.append("remove_node", {"node_id": node_id})
            _LOGGER.debug("Removed storage node %s", node_id)

    # ------------------------------------------------------------------
    def _select_node(self, path: str) -> StorageNode:
        if not self._nodes:
            raise RuntimeError("No storage nodes registered")
        node_ids = sorted(self._nodes.keys())
        index = hash(path) % len(node_ids)
        return self._nodes[node_ids[index]]

    def write(self, path: str, data: bytes) -> None:
        node = self._select_node(path)
        node.driver.write(path, data)
        self._transaction_log.append(
            "write",
            {"path": path, "node_id": node.node_id, "bytes": len(data)},
        )
        _LOGGER.debug("Wrote %s bytes to %s via node %s", len(data), path, node.node_id)

    def read(self, path: str) -> bytes:
        node = self._select_node(path)
        payload = node.driver.read(path)
        self._transaction_log.append("read", {"path": path, "node_id": node.node_id})
        _LOGGER.debug("Read %s bytes from %s via node %s", len(payload), path, node.node_id)
        return payload

    def list(self, prefix: str = "") -> List[str]:
        entries: List[str] = []
        with self._lock:
            for node in self._nodes.values():
                entries.extend(node.driver.list(prefix))
        deduped = sorted(set(entries))
        _LOGGER.debug("Listing prefix %s -> %s entries", prefix, len(deduped))
        return deduped

    def delete(self, path: str) -> None:
        node = self._select_node(path)
        node.driver.delete(path)
        self._transaction_log.append("delete", {"path": path, "node_id": node.node_id})
        _LOGGER.debug("Deleted %s via node %s", path, node.node_id)

    # ------------------------------------------------------------------
    def export_manifest(self) -> str:
        with self._lock:
            manifest = {
                node_id: {
                    "driver": node.driver.name,
                    "capacity": node.capacity_bytes,
                    "metadata": node.metadata,
                }
                for node_id, node in self._nodes.items()
            }
        return json.dumps(manifest, indent=2, sort_keys=True)


__all__ = ["DistributedVirtualFileSystem", "StorageNode", "FileDriver"]
