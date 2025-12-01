from __future__ import annotations

"""Background worker that represents the Eden88 autonomous thread."""

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

TaskHandler = Callable[[str, dict], dict]


@dataclass
class Eden88Task:
    name: str
    payload: dict
    created_at: float = field(default_factory=time.time)


class Eden88AutonomousThread:
    """Simple cooperative worker for Eden88 background rituals."""

    def __init__(self, handler: TaskHandler, *, idle_sleep: float = 0.05) -> None:
        self.handler = handler
        self.idle_sleep = idle_sleep
        self._queue: "queue.Queue[Eden88Task]" = queue.Queue()
        self._history: List[dict] = []
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def history(self) -> List[dict]:
        return list(self._history)

    def submit(self, name: str, payload: Optional[dict] = None) -> None:
        self._queue.put(Eden88Task(name=name, payload=payload or {}))

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run_loop(self) -> None:
        while self._running:
            try:
                task = self._queue.get(timeout=self.idle_sleep)
            except queue.Empty:
                continue

            result = self.handler(task.name, task.payload)
            entry = {
                "name": task.name,
                "payload": task.payload,
                "created_at": task.created_at,
                "completed_at": time.time(),
                "result": result,
            }
            self._history.append(entry)
            self._queue.task_done()
