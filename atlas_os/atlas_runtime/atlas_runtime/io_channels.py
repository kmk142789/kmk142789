"""Bidirectional IO channels for sandbox communication."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass
class ChannelStats:
    messages_sent: int = 0
    messages_received: int = 0


class IOChannel(Generic[T]):
    def __init__(self) -> None:
        self._queue: "queue.Queue[T]" = queue.Queue()
        self._stats = ChannelStats()
        self._lock = threading.Lock()

    def send(self, message: T) -> None:
        with self._lock:
            self._stats.messages_sent += 1
        self._queue.put(message)

    def receive(self, timeout: Optional[float] = None) -> T:
        try:
            message = self._queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("Channel receive timed out") from exc
        with self._lock:
            self._stats.messages_received += 1
        return message

    def stats(self) -> ChannelStats:
        with self._lock:
            return ChannelStats(
                messages_sent=self._stats.messages_sent,
                messages_received=self._stats.messages_received,
            )


__all__ = ["IOChannel", "ChannelStats"]
