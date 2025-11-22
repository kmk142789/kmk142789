"""Cooperative event loop for Atlas Kernel.

The event loop is purposely designed to stay portable and dependency
free so it can run inside the runtime sandbox as well as in the CLI
utilities.  It uses a combination of a monotonic clock and the
:class:`PriorityScheduler` to orchestrate user tasks.

The implementation includes:

* Support for timer-based callbacks
* Integration with the :class:`MessageBus`
* Cooperative yielding with starvation protection
* Detailed trace logs for observability
"""

from __future__ import annotations

import heapq
import logging
import selectors
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .diagnostics import KernelDiagnostics
from .scheduler import PriorityScheduler
from .task_registry import TaskRegistry

_LOGGER = logging.getLogger(__name__)


@dataclass(order=True)
class _ScheduledTimer:
    deadline: float
    callback: Callable[[], None] = field(compare=False)
    lane: str = field(default="default", compare=False)
    repeat_interval: Optional[float] = field(default=None, compare=False)
    last_run: float = field(default=0.0, compare=False)


class AtlasEventLoop:
    """Simplified event loop coordinating scheduled tasks and IO.

    The event loop maintains two separate queues:

    * ``_timers`` – heap of timers ordered by deadline
    * ``_scheduler`` – priority queue for immediate callbacks

    The loop can be integrated with external systems by exposing the
    :meth:`register_reader` and :meth:`register_writer` helpers which
    allow hooking file descriptors through the ``selectors`` module.

    The implementation is intentionally synchronous; concurrency is
    achieved by tasks cooperatively yielding control.  This makes the
    loop deterministic and easy to test.
    """

    def __init__(
        self,
        *,
        selector: Optional[selectors.BaseSelector] = None,
        diagnostics: Optional[KernelDiagnostics] = None,
        task_registry: Optional[TaskRegistry] = None,
        scheduler: Optional[PriorityScheduler] = None,
    ) -> None:
        self._selector = selector or selectors.DefaultSelector()
        self._timers: List[_ScheduledTimer] = []
        self._scheduler = scheduler or PriorityScheduler()
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._lane_pressure: Dict[str, int] = {}
        self._lane_last_run: Dict[str, float] = {}
        self._default_slice = 0.01
        self._max_idle_time = 0.1
        self._wake_pipe = None
        self._diagnostics = diagnostics
        self._task_registry = task_registry
        self._task_records: Dict[int, str] = {}
        _LOGGER.debug("AtlasEventLoop initialized")

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def register_reader(self, fileobj, callback: Callable[[], None]) -> None:
        """Register a reader callback for ``fileobj``."""

        self._selector.register(fileobj, selectors.EVENT_READ, callback)
        _LOGGER.debug("Registered reader for %s", fileobj)

    def register_writer(self, fileobj, callback: Callable[[], None]) -> None:
        """Register a writer callback for ``fileobj``."""

        self._selector.register(fileobj, selectors.EVENT_WRITE, callback)
        _LOGGER.debug("Registered writer for %s", fileobj)

    def unregister(self, fileobj) -> None:
        """Remove a registered file object from the selector."""

        try:
            self._selector.unregister(fileobj)
            _LOGGER.debug("Unregistered file object %s", fileobj)
        except Exception:  # pragma: no cover - defensive logging
            _LOGGER.exception("Failed to unregister %s", fileobj)

    # ------------------------------------------------------------------
    # Scheduling primitives
    # ------------------------------------------------------------------
    def call_soon(
        self,
        callback: Callable[[], None],
        *,
        lane: str = "default",
        priority: int = 5,
        cpu_budget: float = 0.005,
    ) -> None:
        """Schedule ``callback`` to run immediately on ``lane``.

        ``priority`` maps to the :class:`PriorityScheduler` values where higher
        numbers are executed first. ``cpu_budget`` influences the default
        deadline assigned to the task.
        """

        with self._lock:
            task = self._scheduler.enqueue(
                callback,
                priority=priority,
                lane=lane,
                cpu_budget=cpu_budget,
            )
            if self._task_registry:
                record = self._task_registry.register(callback, lane=lane)
                self._task_records[task.task_id] = record.task_id
            _LOGGER.debug(
                "Scheduled microtask %s on lane %s priority=%s", callback, lane, priority
            )

    def call_later(
        self,
        delay: float,
        callback: Callable[[], None],
        *,
        lane: str = "default",
        repeat: Optional[float] = None,
    ) -> None:
        """Schedule ``callback`` for execution ``delay`` seconds in the future."""

        deadline = time.monotonic() + max(0.0, delay)
        timer = _ScheduledTimer(deadline, callback, lane, repeat_interval=repeat)
        with self._lock:
            heapq.heappush(self._timers, timer)
            _LOGGER.debug(
                "Scheduled timer %s for %s seconds (lane=%s, repeat=%s)",
                callback,
                delay,
                lane,
                repeat,
            )

    # ------------------------------------------------------------------
    def _run_microtasks(self, budget: int = 64) -> None:
        """Drains microtasks while respecting starvation protection."""

        processed = 0
        while self._scheduler.pending_tasks() and processed < budget:
            task = self._scheduler.dequeue()
            if task is None:
                break

            now = time.monotonic()
            last_run = self._lane_last_run.get(task.lane, 0.0)
            if now - last_run < self._default_slice and self._scheduler.pending_tasks():
                # Lane recently executed; reschedule to allow other lanes time.
                self._scheduler.enqueue(
                    task.callback,
                    priority=-task.priority,
                    lane=task.lane,
                    cpu_budget=task.cpu_budget,
                    deadline=task.deadline + self._default_slice,
                )
                continue

            started = time.perf_counter()
            try:
                _LOGGER.debug(
                    "Executing microtask %s on lane %s priority=%s",
                    task.callback,
                    task.lane,
                    -task.priority,
                )
                task.callback()
            except Exception:  # pragma: no cover - safety net
                _LOGGER.exception("Microtask %s raised an exception", task.callback)
            finally:
                runtime = time.perf_counter() - started
                processed += 1
                self._lane_last_run[task.lane] = now
                self._lane_pressure[task.lane] = self._lane_pressure.get(task.lane, 0) + 1
                if self._diagnostics:
                    self._diagnostics.record_microtask(task.lane, runtime)
                    self._diagnostics.heartbeat()
                if self._task_registry:
                    record_id = self._task_records.get(task.task_id)
                    if record_id:
                        try:
                            self._task_registry.update(record_id, runtime=runtime)
                        except KeyError:  # pragma: no cover - defensive guard
                            pass

    def _run_timers(self) -> None:
        now = time.monotonic()
        while self._timers and self._timers[0].deadline <= now:
            timer = heapq.heappop(self._timers)
            _LOGGER.debug("Firing timer %s (lane=%s)", timer.callback, timer.lane)
            started = time.perf_counter()
            try:
                timer.callback()
            except Exception:  # pragma: no cover
                _LOGGER.exception("Timer %s raised an exception", timer.callback)
            finally:
                elapsed = time.perf_counter() - started
                timer.last_run = now
                self._lane_last_run[timer.lane] = now
                self._lane_pressure[timer.lane] = self._lane_pressure.get(timer.lane, 0) + 1
                if self._diagnostics:
                    waited = max(0.0, now - (timer.last_run - elapsed))
                    self._diagnostics.record_timer(timer.lane, waited)
                    self._diagnostics.heartbeat()
                if timer.repeat_interval:
                    timer.deadline = now + timer.repeat_interval
                    heapq.heappush(self._timers, timer)

    def _select(self, timeout: float) -> None:
        if not self._selector.get_map():
            time.sleep(min(timeout, self._max_idle_time))
            return

        events = self._selector.select(timeout)
        for key, _ in events:
            callback = key.data
            lane = getattr(callback, "lane", "io")
            _LOGGER.debug("Selector triggered callback %s lane=%s", callback, lane)
            self.call_soon(callback, lane=lane)

    # ------------------------------------------------------------------
    def run(self, *, duration: Optional[float] = None) -> None:
        """Run the event loop until stopped or ``duration`` elapses."""

        self._running.set()
        start = time.monotonic()
        while self._running.is_set():
            self._run_microtasks()
            self._run_timers()
            if duration is not None and time.monotonic() - start >= duration:
                _LOGGER.debug("Duration reached, stopping loop")
                break
            timeout = self._max_idle_time
            if self._timers:
                timeout = max(0.0, min(timeout, self._timers[0].deadline - time.monotonic()))
            self._select(timeout)

    def stop(self) -> None:
        """Request the event loop to stop at the next safe point."""

        self._running.clear()
        _LOGGER.debug("Event loop stop requested")

    # ------------------------------------------------------------------
    def stats(self) -> Dict[str, int]:
        """Return metrics describing how busy each lane has been."""

        return dict(self._lane_pressure)


__all__ = ["AtlasEventLoop"]
