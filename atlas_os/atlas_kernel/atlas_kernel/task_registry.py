"""Task registry tracking metadata for cooperative tasks."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    lane: str
    callback_name: str
    created_at: float
    last_run: float
    runs: int
    total_runtime: float


class TaskRegistry:
    """Registry that records metadata about scheduled tasks."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = threading.RLock()

    def register(self, callback, *, lane: str) -> TaskRecord:
        name = getattr(callback, "__qualname__", repr(callback))
        created = time.time()
        record = TaskRecord(uuid.uuid4().hex, lane, name, created, created, 0, 0.0)
        with self._lock:
            self._tasks[record.task_id] = record
        return record

    def update(self, task_id: str, *, runtime: float) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                raise KeyError(f"Unknown task {task_id}")
            record.last_run = time.time()
            record.runs += 1
            record.total_runtime += max(runtime, 0.0)

    def unregister(self, task_id: str) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)

    def lookup(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def tasks(self) -> Iterable[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())


__all__ = ["TaskRegistry", "TaskRecord"]
