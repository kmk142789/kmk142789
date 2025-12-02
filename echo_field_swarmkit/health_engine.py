"""Offline health and remediation engine."""

from __future__ import annotations

import shutil
from typing import Dict

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - environment may not have psutil
    psutil = None

from .task_ledger import Task


class HealthEngine:
    def __init__(self, node_id: str, task_store, state_store):
        self.node_id = node_id
        self.task_store = task_store
        self.state_store = state_store

    def run_health_check_cycle(self) -> Dict[str, bool]:
        """Run checks, update node state, and emit remediation tasks."""
        checks = {
            "disk_ok": self._check_disk(),
            "cpu_ok": self._check_cpu(),
            "memory_ok": self._check_memory(),
        }

        self.state_store.update_health_summary(checks)

        if not checks["disk_ok"]:
            self._emit_cleanup_disk_task()
        if not checks["cpu_ok"]:
            self._emit_cpu_relief_task()
        if not checks["memory_ok"]:
            self._emit_memory_cleanup_task()

        return checks

    def _check_disk(self) -> bool:
        total, _, free = shutil.disk_usage("/")
        return free / total > 0.05

    def _check_cpu(self) -> bool:
        if psutil is None:
            return True
        return psutil.cpu_percent(interval=1) < 90

    def _check_memory(self) -> bool:
        if psutil is None:
            return True
        mem = psutil.virtual_memory()
        return mem.percent < 90

    def _emit_cleanup_disk_task(self):
        self._save_task(
            Task.new(
                type_="cleanup_disk",
                payload={"min_free_ratio": 0.1},
                origin_node=self.node_id,
            )
        )

    def _emit_cpu_relief_task(self):
        self._save_task(
            Task.new(
                type_="cpu_relief",
                payload={"cooldown_seconds": 10},
                origin_node=self.node_id,
            )
        )

    def _emit_memory_cleanup_task(self):
        self._save_task(
            Task.new(
                type_="memory_cleanup",
                payload={"target_usage_percent": 80},
                origin_node=self.node_id,
            )
        )

    def _save_task(self, task: Task):
        self.task_store.save(task)
