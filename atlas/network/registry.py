"""Node registry for Atlas OS network service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional


@dataclass(slots=True)
class NodeInfo:
    id: str
    host: str
    port: int
    weight: float = 1.0
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: Dict[str, str] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: Dict[str, NodeInfo] = {}

    def register(self, node: NodeInfo) -> None:
        node.last_seen = datetime.now(timezone.utc)
        self._nodes[node.id] = node

    def unregister(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)

    def list(self) -> Iterable[NodeInfo]:
        return list(self._nodes.values())

    def get(self, node_id: str) -> Optional[NodeInfo]:
        return self._nodes.get(node_id)

    def heartbeat(self, node_id: str, weight: Optional[float] = None) -> None:
        node = self._nodes.get(node_id)
        if not node:
            return
        node.last_seen = datetime.now(timezone.utc)
        if weight is not None:
            node.weight = weight


__all__ = ["NodeRegistry", "NodeInfo"]
