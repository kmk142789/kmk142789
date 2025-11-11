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
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, List, Optional, Tuple

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
    * ``_microtask_queue`` – deque of callbacks to run immediately

    The loop can be integrated with external systems by exposing the
    :meth:`register_reader` and :meth:`register_writer` helpers which
    allow hooking file descriptors through the ``selectors`` module.

    The implementation is intentionally synchronous; concurrency is
    achieved by tasks cooperatively yielding control.  This makes the
    loop deterministic and easy to test.
    """

    def __init__(self, *, selector: Optional[selectors.BaseSelector] = None) -> None:
        self._selector = selector or selectors.DefaultSelector()
        self._timers: List[_ScheduledTimer] = []
        self._microtask_queue: Deque[Tuple[Callable[[], None], str]] = deque()
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._lane_pressure: Dict[str, int] = {}
        self._lane_last_run: Dict[str, float] = {}
        self._default_slice = 0.01
        self._max_idle_time = 0.1
        self._wake_pipe = None
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
    def call_soon(self, callback: Callable[[], None], *, lane: str = "default") -> None:
        """Schedule ``callback`` to run immediately on ``lane``."""

        with self._lock:
            self._microtask_queue.append((callback, lane))
            _LOGGER.debug("Scheduled microtask %s on lane %s", callback, lane)

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
        while self._microtask_queue and processed < budget:
            callback, lane = self._microtask_queue.popleft()
            now = time.monotonic()
            last_run = self._lane_last_run.get(lane, 0.0)
            if now - last_run < self._default_slice and self._microtask_queue:
                # Push task to tail to avoid monopolizing lane.
                self._microtask_queue.append((callback, lane))
                continue
            try:
                _LOGGER.debug("Executing microtask %s on lane %s", callback, lane)
                callback()
            except Exception:  # pragma: no cover - safety net
                _LOGGER.exception("Microtask %s raised an exception", callback)
            finally:
                processed += 1
                self._lane_last_run[lane] = now
                self._lane_pressure[lane] = self._lane_pressure.get(lane, 0) + 1

    def _run_timers(self) -> None:
        now = time.monotonic()
        while self._timers and self._timers[0].deadline <= now:
            timer = heapq.heappop(self._timers)
            _LOGGER.debug("Firing timer %s (lane=%s)", timer.callback, timer.lane)
            try:
                timer.callback()
            except Exception:  # pragma: no cover
                _LOGGER.exception("Timer %s raised an exception", timer.callback)
            finally:
                timer.last_run = now
                self._lane_last_run[timer.lane] = now
                self._lane_pressure[timer.lane] = self._lane_pressure.get(timer.lane, 0) + 1
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
