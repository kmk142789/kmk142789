"""Asynchronous task runner with simple DAG semantics."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict


AsyncCallable = Callable[[], Awaitable[Any] | Any]


@dataclass
class TaskSpec:
    name: str
    deps: list[str] = field(default_factory=list)
    fn: AsyncCallable = lambda: asyncio.sleep(0)


class Runner:
    def __init__(self, policy, receipts) -> None:
        self.policy = policy
        self.receipts = receipts

    async def execute(self, graph: Dict[str, TaskSpec]) -> None:
        done: set[str] = set()
        while len(done) < len(graph):
            progress = False
            for name, spec in graph.items():
                if name in done:
                    continue
                if any(dep not in done for dep in spec.deps):
                    continue
                if not self._policy_allows(name):
                    continue

                try:
                    await self._run_task(spec)
                    self.receipts.commit("task.ok", {"name": name})
                except Exception as exc:  # pragma: no cover - defensive branch
                    self.receipts.commit("task.fail", {"name": name, "err": str(exc)})
                    await asyncio.sleep(1)
                finally:
                    done.add(name)
                    progress = True

            if not progress:
                break

    async def _run_task(self, spec: TaskSpec) -> None:
        result = spec.fn()
        if asyncio.iscoroutine(result) or isinstance(result, asyncio.Future):
            await result
        else:
            await asyncio.to_thread(lambda: result)

    def _policy_allows(self, task_name: str) -> bool:
        decide = getattr(self.policy, "decide", None)
        if callable(decide):
            try:
                return decide(task_name, risk_score=2) != "deny"
            except Exception:
                return True
        return True


__all__ = ["Runner", "TaskSpec"]
