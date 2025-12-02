"""Task data model and helpers for the swarm ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import time
import uuid


@dataclass
class Task:
    id: str
    type: str  # "health_check", "patch", "sync_logs", etc.
    payload: Dict[str, Any]
    created_at: float
    updated_at: float
    status: str  # "pending", "running", "done", "failed"
    origin_node: str
    version: int = 0  # for conflict resolution

    @staticmethod
    def new(type_: str, payload: Dict[str, Any], origin_node: str) -> "Task":
        """Create a new task with timestamps and a UUID."""
        now = time.time()
        return Task(
            id=str(uuid.uuid4()),
            type=type_,
            payload=payload,
            created_at=now,
            updated_at=now,
            status="pending",
            origin_node=origin_node,
            version=0,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        """Safely reconstruct a Task from a dictionary."""
        return Task(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "origin_node": self.origin_node,
            "version": self.version,
        }
