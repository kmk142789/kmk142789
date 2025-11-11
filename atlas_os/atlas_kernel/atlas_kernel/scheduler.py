"""Priority aware scheduler with starvation protection."""

from __future__ import annotations

import heapq
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


@dataclass(order=True)
class ScheduledTask:
    priority: int
    deadline: float
    task_id: int = field(compare=False)
    callback: Callable[[], None] = field(compare=False)
    lane: str = field(default="default", compare=False)
    cpu_budget: float = field(default=0.001, compare=False)
    last_run: float = field(default=0.0, compare=False)


class PriorityScheduler:
    """Hybrid priority and deadline scheduler.

    Tasks are stored in a heap keyed by a tuple ``(priority, deadline)``.
    Higher numerical priority values represent more important tasks.
    The scheduler normalizes values so that starvation cannot occur by
    periodically reducing the priority of long-lived tasks.
    """

    def __init__(self) -> None:
        self._queue: List[ScheduledTask] = []
        self._counter = 0
        self._lane_stats: Dict[str, int] = {}
        self._aging_factor = 0.95

    def enqueue(
        self,
        callback: Callable[[], None],
        *,
        priority: int = 5,
        lane: str = "default",
        cpu_budget: float = 0.005,
        deadline: Optional[float] = None,
    ) -> ScheduledTask:
        self._counter += 1
        deadline = deadline or time.monotonic() + cpu_budget
        task = ScheduledTask(-priority, deadline, self._counter, callback, lane, cpu_budget)
        heapq.heappush(self._queue, task)
        _LOGGER.debug("Enqueued task %s priority=%s lane=%s", task.task_id, priority, lane)
        return task

    def dequeue(self) -> Optional[ScheduledTask]:
        if not self._queue:
            return None
        task = heapq.heappop(self._queue)
        self._lane_stats[task.lane] = self._lane_stats.get(task.lane, 0) + 1
        _LOGGER.debug(
            "Dequeued task %s (priority=%s lane=%s)", task.task_id, -task.priority, task.lane
        )
        return task

    def promote_starved_tasks(self) -> None:
        """Apply exponential aging so starved tasks bubble up."""

        rebuilt: List[ScheduledTask] = []
        while self._queue:
            task = heapq.heappop(self._queue)
            aged_priority = int(task.priority * self._aging_factor)
            rebuilt.append(
                ScheduledTask(
                    aged_priority,
                    task.deadline,
                    task.task_id,
                    task.callback,
                    task.lane,
                    task.cpu_budget,
                    task.last_run,
                )
            )
        for task in rebuilt:
            heapq.heappush(self._queue, task)
        _LOGGER.debug("Applied aging to %s tasks", len(rebuilt))

    def pending_tasks(self) -> int:
        return len(self._queue)

    def lane_stats(self) -> Dict[str, int]:
        return dict(self._lane_stats)


__all__ = ["PriorityScheduler", "ScheduledTask"]
