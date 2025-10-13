"""Structured event emission utilities."""

from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any, Dict


_EVENT_QUEUE: "queue.Queue[dict[str, Any]]" = queue.Queue(maxsize=1000)


def emit(kind: str, data: Dict[str, Any]) -> None:
    event = {"ts": time.time(), "kind": kind, "data": data}
    try:
        _EVENT_QUEUE.put_nowait(event)
    except queue.Full:  # pragma: no cover - defensive drop
        pass


def background_writer(path: str = "ECHO_LOG.ndjson") -> threading.Thread:
    def run() -> None:
        with open(path, "a", encoding="utf-8") as handle:
            while True:
                event = _EVENT_QUEUE.get()
                handle.write(json.dumps(event) + "\n")
                handle.flush()

    thread = threading.Thread(target=run, name="echo-observe-writer", daemon=True)
    thread.start()
    return thread


__all__ = ["emit", "background_writer"]
