"""Autonomous task lists that bind identity and memory persistence.

This module introduces an identity-anchored task list that records every
mutation into the real-time memory store. Tasks can be generated from a set
of objectives, updated as they progress, and exported for orchestration
layers that need a durable view of Echo's commitments.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional, Sequence

from .memory.store import JsonMemoryStore
from .sovereign_identity_kernel import CapabilityIdentityKernel, IdentityKernelSnapshot


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _runtime_root() -> Path:
    env = os.getenv("ECHO_RUNTIME_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".echo-runtime"


def _default_task_path() -> Path:
    env = os.getenv("ECHO_TASK_PATH")
    if env:
        return Path(env)
    return _runtime_root() / "tasks" / "autonomous_tasks.json"


@dataclass(slots=True)
class AutonomousTask:
    """Structured task aligned to Echo's sovereign identity."""

    task_id: str
    title: str
    objective: str
    status: str = "pending"
    priority: str = "medium"
    owner_did: str | None = None
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    memory_anchor: str | None = None
    identity: Mapping[str, Any] | None = None

    def to_dict(self) -> MutableMapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "task_id": self.task_id,
            "title": self.title,
            "objective": self.objective,
            "status": self.status,
            "priority": self.priority,
            "owner_did": self.owner_did,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memory_anchor": self.memory_anchor,
            "identity": dict(self.identity) if self.identity else None,
        }
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AutonomousTask":
        return cls(
            task_id=str(payload["task_id"]),
            title=str(payload["title"]),
            objective=str(payload.get("objective", "")),
            status=str(payload.get("status", "pending")),
            priority=str(payload.get("priority", "medium")),
            owner_did=payload.get("owner_did"),
            created_at=str(payload.get("created_at", _utcnow())),
            updated_at=str(payload.get("updated_at", _utcnow())),
            memory_anchor=payload.get("memory_anchor"),
            identity=payload.get("identity"),
        )

    def mark_status(self, status: str, *, memory_anchor: str | None = None) -> None:
        self.status = status
        self.updated_at = _utcnow()
        if memory_anchor:
            self.memory_anchor = memory_anchor


class AutonomousTaskList:
    """Identity-anchored task list with real-time memory persistence."""

    def __init__(
        self,
        identity_source: CapabilityIdentityKernel | IdentityKernelSnapshot | Mapping[str, Any],
        *,
        storage_path: Path | str | None = None,
        memory_store: JsonMemoryStore | None = None,
    ) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else _default_task_path()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_store = memory_store or JsonMemoryStore()
        self._identity_snapshot = self._coerce_identity_snapshot(identity_source)
        self._tasks: dict[str, AutonomousTask] = {}
        self._load_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def plan_tasks(
        self,
        objectives: Sequence[str],
        *,
        owner_did: Optional[str] = None,
        priority: str = "medium",
    ) -> Sequence[AutonomousTask]:
        """Create tasks for each objective and persist them immediately."""

        planned: list[AutonomousTask] = []
        default_owner = owner_did or self._identity_snapshot.get("issuer_did")
        for objective in objectives:
            task = AutonomousTask(
                task_id=self._new_task_id(),
                title=objective,
                objective=objective,
                priority=priority,
                owner_did=default_owner,
                identity=self._identity_snapshot,
            )
            anchor = self._record_memory("create_task", task, summary=f"Task created: {objective}")
            task.mark_status(task.status, memory_anchor=anchor)
            self._tasks[task.task_id] = task
            planned.append(task)
        self._persist_state()
        return planned

    def ensure_persistent_system_tasks(
        self,
        *,
        owner_did: Optional[str] = None,
        priority: str = "high",
    ) -> Sequence[AutonomousTask]:
        """Seed long-lived optimization and maintenance tasks if missing.

        This helper protects core operational objectives by ensuring Echo always
        tracks system optimization, dependency upgrades, and health maintenance
        across memory and telemetry. Tasks are only created when they do not yet
        exist in the persisted task ledger, preventing duplicate inserts while
        still recording memory anchors for any newly added work.
        """

        persistent_objectives = (
            "Optimize autonomous policy bundles and convergence thresholds",
            "Upgrade sovereign runtime dependencies and apply security patches",
            "Maintain telemetry, memory, and ledger health across nodes",
        )
        missing = [
            objective
            for objective in persistent_objectives
            if not self._has_task_with_objective(objective)
        ]

        if not missing:
            return []

        return self.plan_tasks(missing, owner_did=owner_did, priority=priority)

    def advance_task(self, task_id: str, *, status: str, note: str | None = None) -> AutonomousTask:
        """Update a task status, recording the change into memory."""

        if task_id not in self._tasks:
            raise KeyError(f"unknown task: {task_id}")
        task = self._tasks[task_id]
        summary = note or f"{task.title} is now {status}"
        anchor = self._record_memory("update_task", task, summary=summary, status=status)
        task.mark_status(status, memory_anchor=anchor)
        self._persist_state()
        return task

    def export(self) -> Mapping[str, Any]:
        """Return the persisted payload for orchestration layers."""

        return {
            "identity": self._identity_snapshot,
            "tasks": [task.to_dict() for task in self._tasks.values()],
        }

    def tasks(self) -> Sequence[AutonomousTask]:
        return tuple(self._tasks.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        if not self.storage_path.exists():
            self._persist_state()
            return
        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self._identity_snapshot = payload.get("identity", self._identity_snapshot)
        tasks = payload.get("tasks", [])
        self._tasks = {entry["task_id"]: AutonomousTask.from_dict(entry) for entry in tasks}

    def _persist_state(self) -> None:
        payload = self.export()
        self.storage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _has_task_with_objective(self, objective: str) -> bool:
        return any(task.objective == objective for task in self._tasks.values())

    def _record_memory(
        self,
        event: str,
        task: AutonomousTask,
        *,
        summary: str,
        status: str | None = None,
    ) -> str:
        metadata: dict[str, Any] = {
            "intent": "autonomous-task",
            "task_id": task.task_id,
            "status": status or task.status,
            "owner": task.owner_did,
            "issuer_did": self._identity_snapshot.get("issuer_did"),
        }
        command_detail = f"{task.title} — {task.objective}"
        with self.memory_store.session(metadata=metadata) as session:
            session.set_artifact(self.storage_path)
            session.set_summary(summary)
            command = session.record_command(event, detail=command_detail)
        return command["recorded_at"]

    def _coerce_identity_snapshot(
        self, source: CapabilityIdentityKernel | IdentityKernelSnapshot | Mapping[str, Any]
    ) -> Mapping[str, Any]:
        snapshot: Mapping[str, Any] | IdentityKernelSnapshot | None
        if isinstance(source, CapabilityIdentityKernel):
            snapshot = source.snapshot()
        elif hasattr(source, "snapshot"):
            snapshot = source.snapshot()  # type: ignore[assignment]
        else:
            snapshot = source

        if isinstance(snapshot, IdentityKernelSnapshot):
            return {
                "issuer_did": snapshot.issuer_did,
                "shared_command_secret": snapshot.shared_command_secret,
                "identity_state": dict(snapshot.identity_state),
            }
        if isinstance(snapshot, Mapping):
            return dict(snapshot)
        raise TypeError("identity_source must be a CapabilityIdentityKernel, IdentityKernelSnapshot, or mapping")

    def _new_task_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"echo-task-{timestamp}-{uuid.uuid4().hex[:6]}"
