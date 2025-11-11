"""Process isolation wrapper for sandbox execution."""

from __future__ import annotations

import multiprocessing as mp
from typing import Iterable, Tuple

from .sandbox import Sandbox, SandboxResult


def _worker(program, memory_limit, timeout, queue):
    sandbox = Sandbox()
    try:
        result = sandbox.execute(program, memory_limit=memory_limit, timeout=timeout)
        queue.put((True, result))
    except Exception as exc:  # pragma: no cover - error path
        queue.put((False, str(exc)))


class ProcessIsolator:
    def run(
        self,
        program: Iterable[Tuple[str, int | None]],
        *,
        memory_limit: int = 1024,
        timeout: float = 0.2,
    ) -> SandboxResult:
        queue: mp.Queue = mp.Queue()
        proc = mp.Process(
            target=_worker,
            args=(list(program), memory_limit, timeout, queue),
        )
        proc.start()
        proc.join(timeout + 0.1)
        if proc.is_alive():
            proc.terminate()
            proc.join()
            raise TimeoutError("Process isolation timeout")
        success, payload = queue.get()
        if not success:
            raise RuntimeError(payload)
        return payload


__all__ = ["ProcessIsolator"]
