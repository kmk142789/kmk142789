"""Node agent that runs health checks, task execution, and swarm sync."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from .health_engine import HealthEngine
from .storage import StateStore, TaskStore
from .swarm_protocol import SwarmProtocol
from .task_ledger import Task

logger = logging.getLogger(__name__)


class FileSyncAdapter:
    """
    Simple file-drop sync adapter.

    Each node writes its exported state to `<sync_path>/<node_id>.json` and
    attempts to read peer files from the same directory. This works offline
    for demos, USB handoffs, or shared folders.
    """

    def __init__(self, node_id: str, sync_path: str):
        self.node_id = node_id
        self.sync_path = os.path.abspath(os.path.expanduser(sync_path))
        os.makedirs(self.sync_path, exist_ok=True)

    def publish(self, state: dict) -> None:
        path = os.path.join(self.sync_path, f"{self.node_id}.json")
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, path)

    def fetch(self, peer_id: str) -> Optional[dict]:
        path = os.path.join(self.sync_path, f"{peer_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Peer state file for %s is corrupt; skipping", peer_id)
            return None

    def discover_peers(self) -> Iterable[str]:
        for filename in os.listdir(self.sync_path):
            if not filename.endswith(".json"):
                continue
            peer_id = filename[:-5]
            if peer_id != self.node_id:
                yield peer_id


@dataclass
class EchoNodeConfig:
    node_id: str
    task_store_path: str
    state_store_path: str
    sync_path: str
    health_interval: int = 300
    sync_interval: int = 60
    max_sync_age: int = 900
    peers: Optional[Iterable[str]] = None


class EchoNode:
    def __init__(self, config: EchoNodeConfig):
        self.node_id = config.node_id
        self.tasks = TaskStore(self.node_id, config.task_store_path)
        self.state = StateStore(self.node_id, config.state_store_path)
        self.swarm = SwarmProtocol(self.node_id, self.tasks, self.state)
        self.health = HealthEngine(self.node_id, self.tasks, self.state)
        self.sync_adapter = FileSyncAdapter(self.node_id, config.sync_path)
        self.health_interval = config.health_interval
        self.sync_interval = config.sync_interval
        self.max_sync_age = config.max_sync_age

        for peer in config.peers or []:
            self.state.record_peer(peer)

    def main_loop(self):
        last_sync = 0
        last_health = 0

        while True:
            now = time.time()

            if now - last_health > self.health_interval:
                checks = self.health.run_health_check_cycle()
                logger.info("Health checks: %s", checks)
                last_health = now

            if now - last_sync > self.sync_interval:
                self._sync_with_peers()
                last_sync = now

            self._execute_local_tasks()
            time.sleep(1)

    def _sync_with_peers(self):
        local_state = self.swarm.export_state()
        self.sync_adapter.publish(local_state)
        discovered_peers = set(self.sync_adapter.discover_peers())
        for peer in set(self.state.get_peers()) | discovered_peers:
            remote = self.sync_adapter.fetch(peer)
            if not remote:
                continue
            last_seen = remote.get("node_state", {}).get("last_seen", 0)
            age = time.time() - last_seen
            if age > self.max_sync_age:
                logger.info(
                    "Skipping peer %s due to stale snapshot (age=%.0fs > %ss)",
                    peer,
                    age,
                    self.max_sync_age,
                )
                continue
            self.swarm.import_state(remote)
            logger.info("Merged state from peer %s", peer)
            self.state.record_peer(peer)

    def _execute_local_tasks(self):
        for task in self.tasks.get_pending_for_node(self.node_id):
            success = self._handle_task(task)
            task.status = "done" if success else "failed"
            task.version += 1
            task.updated_at = time.time()
            self.tasks.save(task)

    def _handle_task(self, task: Task) -> bool:
        if task.type == "cleanup_disk":
            return self._cleanup_disk(task.payload)
        if task.type == "cpu_relief":
            return self._cpu_cooldown(task.payload)
        if task.type == "memory_cleanup":
            return self._memory_cleanup(task.payload)
        logger.info("No handler for task %s", task.type)
        return False

    def _cleanup_disk(self, payload: dict) -> bool:
        target_free = float(payload.get("min_free_ratio", 0.1))
        temp_dir = "/tmp/echo_field_swarmkit"
        os.makedirs(temp_dir, exist_ok=True)
        removed_bytes = 0
        for root, _, files in os.walk(temp_dir):
            for name in files:
                path = os.path.join(root, name)
                try:
                    removed_bytes += os.path.getsize(path)
                    os.remove(path)
                except OSError:
                    continue
        logger.info("Disk cleanup removed %.2f KB from %s", removed_bytes / 1024, temp_dir)
        try:
            stat = os.statvfs("/")
            free_ratio = (stat.f_bavail * stat.f_frsize) / (stat.f_blocks * stat.f_frsize)
        except OSError:
            free_ratio = 1.0
        return free_ratio >= target_free

    def _cpu_cooldown(self, payload: dict) -> bool:
        cooldown = int(payload.get("cooldown_seconds", 5))
        logger.info("CPU relief: sleeping for %s seconds", cooldown)
        time.sleep(min(cooldown, 30))
        return True

    def _memory_cleanup(self, payload: dict) -> bool:
        logger.info("Memory cleanup stub executed with payload=%s", payload)
        return True
