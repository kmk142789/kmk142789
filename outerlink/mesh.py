from __future__ import annotations

"""Mesh network orchestration for OuterLink runtimes.

The mesh coordinates multiple :class:`OuterLinkRuntime` instances so they can
share state, execute tasks cooperatively, and survive intermittent connectivity.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .runtime import OuterLinkRuntime


@dataclass
class MeshNode:
    """Represents a single OuterLink participant in the mesh."""

    name: str
    runtime: OuterLinkRuntime
    tags: frozenset[str] = field(default_factory=frozenset)
    last_seen: float = field(default_factory=time.time)
    online: bool = True

    def heartbeat(self) -> dict:
        """Collect metrics from the runtime and update heartbeat metadata."""

        state = self.runtime.emit_state()
        self.last_seen = time.time()
        self.online = state.get("online", False)
        return state


class OuterLinkMeshNetwork:
    """Lightweight coordinator that keeps multiple OuterLink runtimes in sync."""

    def __init__(self) -> None:
        self._nodes: Dict[str, MeshNode] = {}
        self._observers: List[Callable[[str, dict], None]] = []
        self._lock = threading.RLock()

    def register(self, name: str, runtime: OuterLinkRuntime, *, tags: Optional[Iterable[str]] = None) -> None:
        """Attach a runtime to the mesh with optional discovery tags."""

        mesh_node = MeshNode(name=name, runtime=runtime, tags=frozenset(tags or []))
        with self._lock:
            self._nodes[name] = mesh_node
        self._notify("registered", {"name": name, "tags": sorted(mesh_node.tags)})

    def unregister(self, name: str) -> None:
        with self._lock:
            self._nodes.pop(name, None)
        self._notify("unregistered", {"name": name})

    def add_observer(self, callback: Callable[[str, dict], None]) -> None:
        self._observers.append(callback)

    def broadcast_task(self, task: str, payload: Optional[dict] = None) -> Dict[str, dict]:
        """Send a task to every registered runtime and collect responses."""

        responses: Dict[str, dict] = {}
        with self._lock:
            nodes = list(self._nodes.items())

        for name, mesh_node in nodes:
            try:
                responses[name] = mesh_node.runtime.handle_task(task, payload)
            except Exception as exc:  # pragma: no cover - resilience logging
                responses[name] = {"task": task, "error": str(exc)}
        self._notify("broadcast", {"task": task, "payload": payload or {}, "responses": responses})
        return responses

    def aggregate_health(self) -> dict:
        """Return mesh-wide heartbeat data and per-node metrics."""

        per_node: Dict[str, dict] = {}
        with self._lock:
            nodes = list(self._nodes.items())

        for name, mesh_node in nodes:
            per_node[name] = mesh_node.heartbeat()
        mesh_online = any(node.online for node in self._nodes.values())
        oldest_heartbeat = min((node.last_seen for node in self._nodes.values()), default=time.time())
        self._notify("health", {"mesh_online": mesh_online, "nodes": per_node})
        return {
            "mesh_online": mesh_online,
            "nodes": per_node,
            "staleness_seconds": max(0.0, time.time() - oldest_heartbeat),
            "total_nodes": len(self._nodes),
        }

    def _notify(self, event: str, payload: dict) -> None:
        for observer in self._observers:
            observer(event, payload)
