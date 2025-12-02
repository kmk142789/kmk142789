"""Lightweight JSON persistence for tasks and node state."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .task_ledger import Task

_LOCK = threading.Lock()


def _expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


@dataclass
class NodeState:
    node_id: str
    hostname: str
    last_seen: float
    health_summary: Dict[str, object]
    swarm_peers: Dict[str, float]  # peer_id -> last_seen

    @staticmethod
    def default(node_id: str) -> "NodeState":
        return NodeState(
            node_id=node_id,
            hostname=socket.gethostname(),
            last_seen=time.time(),
            health_summary={},
            swarm_peers={},
        )


class TaskStore:
    def __init__(self, node_id: str, path: str):
        self.node_id = node_id
        self.path = _expand(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._tasks: Dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with _LOCK:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        self._tasks = {item["id"]: Task.from_dict(item) for item in raw}

    def _persist(self) -> None:
        with _LOCK:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self._tasks.values()], f, indent=2)

    def get_all(self) -> List[Task]:
        return list(self._tasks.values())

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task
        self._persist()

    def get_pending_for_node(self, node_id: str) -> List[Task]:
        return [t for t in self._tasks.values() if t.status == "pending" and t.origin_node == node_id]


class StateStore:
    def __init__(self, node_id: str, path: str):
        self.node_id = node_id
        self.path = _expand(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._state: NodeState = NodeState.default(node_id)
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with _LOCK:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        self._state = NodeState(**raw)

    def _persist(self) -> None:
        with _LOCK:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(asdict(self._state), f, indent=2)

    def get(self) -> NodeState:
        return self._state

    def merge_remote_state(self, remote_state: Optional[Dict[str, object]]) -> None:
        if not remote_state:
            return
        remote_last_seen = remote_state.get("last_seen", 0)
        if remote_last_seen > self._state.last_seen:
            self._state.health_summary = remote_state.get("health_summary", {})
            self._state.last_seen = remote_last_seen
            self._state.swarm_peers.update(remote_state.get("swarm_peers", {}))
            self._persist()

        remote_node_id = remote_state.get("node_id")
        if remote_node_id:
            self._state.swarm_peers[remote_node_id] = time.time()
            self._persist()

    def update_health_summary(self, summary: Dict[str, object]) -> None:
        self._state.health_summary = summary
        self._state.last_seen = time.time()
        self._persist()

    def get_peers(self) -> List[str]:
        return list(self._state.swarm_peers.keys())

    def record_peer(self, peer_id: str) -> None:
        self._state.swarm_peers[peer_id] = time.time()
        self._persist()
