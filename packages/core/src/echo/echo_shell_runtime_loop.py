from __future__ import annotations

"""Runtime loop utilities for orchestrating EchoShell interactions."""

import threading
import time
from typing import Callable, List, Sequence

from ..echoshell import echo_reply

EventHook = Callable[[str, dict], None]


class EchoShellRuntimeLoop:
    """Cooperative runtime loop around the interactive EchoShell primitives."""

    def __init__(self, *, tick_interval: float = 1.0) -> None:
        self.tick_interval = tick_interval
        self._observers: List[EventHook] = []
        self._running = False
        self._start_time: float | None = None
        self._thread: threading.Thread | None = None

    def add_observer(self, hook: EventHook) -> None:
        self._observers.append(hook)

    def run_commands(self, commands: Sequence[str]) -> list[str]:
        """Execute a sequence of commands through ``echo_reply`` and return responses."""

        transcript: list[str] = []
        for index, command in enumerate(commands, start=1):
            response = echo_reply(command)
            transcript.append(response)
            self._emit("command", {"index": index, "command": command, "response": response})
            time.sleep(0.05)
        return transcript

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._emit("started", {"tick_interval": self.tick_interval})

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        uptime = self.uptime_seconds
        self._emit("stopped", {"uptime_seconds": uptime})

    @property
    def uptime_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return max(0.0, time.time() - self._start_time)

    def _loop(self) -> None:
        while self._running:
            self._emit(
                "tick",
                {
                    "uptime_seconds": self.uptime_seconds,
                    "tick_interval": self.tick_interval,
                },
            )
            time.sleep(self.tick_interval)

    def _emit(self, event: str, payload: dict) -> None:
        for hook in self._observers:
            try:
                hook(event, payload)
            except Exception:
                continue
