"""Event loop watchdog detecting stalls."""

from __future__ import annotations

import threading
import time
from typing import Callable


class EventLoopWatchdog:
    """Monitors an event loop and triggers callbacks on stalls."""

    def __init__(self, heartbeat_supplier: Callable[[], float], *, threshold: float = 0.5) -> None:
        self._heartbeat_supplier = heartbeat_supplier
        self._threshold = threshold
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop = threading.Event()
        self._listeners: list[Callable[[float], None]] = []

    def add_listener(self, callback: Callable[[float], None]) -> None:
        self._listeners.append(callback)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            delay = self._heartbeat_supplier()
            if delay > self._threshold:
                for callback in list(self._listeners):
                    try:
                        callback(delay)
                    except Exception:  # pragma: no cover - defensive guard
                        continue
            time.sleep(self._threshold / 2)


__all__ = ["EventLoopWatchdog"]
