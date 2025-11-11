"""Flow control primitives for network messaging."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(slots=True)
class RateWindow:
    tokens: float
    last_refill: float


class TokenBucketLimiter:
    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self._rate = rate
        self._capacity = capacity or rate
        now = time.monotonic()
        self._window = RateWindow(self._capacity, now)
        self._lock = threading.RLock()

    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            self._refill()
            if tokens > self._window.tokens:
                return False
            self._window.tokens -= tokens
            return True

    def available(self) -> float:
        with self._lock:
            self._refill()
            return self._window.tokens

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._window.last_refill
        if elapsed <= 0:
            return
        self._window.tokens = min(self._capacity, self._window.tokens + elapsed * self._rate)
        self._window.last_refill = now


__all__ = ["TokenBucketLimiter"]
