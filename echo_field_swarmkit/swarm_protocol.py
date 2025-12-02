"""Gossip-style synchronization protocol for tasks and node state."""

from __future__ import annotations

from typing import Dict

from .task_ledger import Task


class SwarmProtocol:
    """
    Very simple gossip-style sync:
    - serialize tasks + node_state into compact dict
    - exchange over any transport (HTTP, TCP, file drop, etc.)
    - merge with local using version/updated_at precedence
    """

    def __init__(self, node_id: str, task_store, state_store):
        self.node_id = node_id
        self.task_store = task_store  # abstraction over local storage
        self.state_store = state_store

    def export_state(self) -> Dict:
        return {
            "node_id": self.node_id,
            "tasks": [t.to_dict() for t in self.task_store.get_all()],
            "node_state": self.state_store.get().__dict__,
        }

    def import_state(self, remote_state: Dict):
        for t in remote_state.get("tasks", []):
            self._merge_task(Task.from_dict(t))
        self.state_store.merge_remote_state(remote_state.get("node_state"))

    def _merge_task(self, remote_task: Task):
        local = self.task_store.get(remote_task.id)
        if local is None:
            self.task_store.save(remote_task)
            return

        if remote_task.version > local.version:
            self.task_store.save(remote_task)
        elif remote_task.version == local.version and remote_task.updated_at > local.updated_at:
            self.task_store.save(remote_task)
