from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .broker import ExecutionBroker
from .dsi import DeviceSurfaceInterface
from .events import EventBus
from .router import TaskRouter
from .utils import OfflineState, SafeModeConfig


class OuterLinkRuntime:
    """Offline-first coordinator that binds router, broker, and event system."""

    def __init__(self, config: Optional[SafeModeConfig] = None, offline_state: Optional[OfflineState] = None) -> None:
        self.config = config or SafeModeConfig()
        self.offline_state = offline_state or OfflineState()
        self.event_bus = EventBus(max_history=self.config.event_history_limit)
        self.dsi = DeviceSurfaceInterface(self.config)
        self.broker = ExecutionBroker(self.config, self.dsi, self.event_bus, self.offline_state)
        self.router = TaskRouter(self.event_bus, self.offline_state)
        self._last_flush_index = 0
        self._bootstrap_default_mappings()

    def _bootstrap_default_mappings(self) -> None:
        self.router.register_module("device_status", "dsi")
        self.router.register_module("optimization_tick", "optimizer")
        self.router.register_module("policy_eval", "governance")

    def emit_state(self) -> Dict[str, Any]:
        metrics = self.dsi.get_metrics()
        self.offline_state.enforce_backpressure(self.config.pending_backlog_hard_limit)
        offline_snapshot = self.offline_state.status(
            self.config.offline_cache_dir, self.config.offline_cache_ttl_seconds
        )

        backlog_ok = offline_snapshot["pending_events"] <= self.config.pending_backlog_threshold
        self.offline_state.record_health_check(
            "pending_event_backlog",
            passed=backlog_ok,
            details=(
                "pending events within guardrails"
                if backlog_ok
                else f"{offline_snapshot['pending_events']} events waiting for flush"
            ),
        )

        cache_healthy = not bool(offline_snapshot["cache_stale"])
        self.offline_state.record_health_check(
            "cache_health",
            passed=cache_healthy,
            details="offline cache within ttl" if cache_healthy else "offline cache stale",
        )

        capability_report = offline_snapshot.get("capability_report", {})
        replay_ready = capability_report.get("replay_ready", False)
        cache_present = self.config.offline_cache_dir.exists()
        self.offline_state.refresh_dynamic_capabilities(
            cache_present=cache_present,
            cache_stale=offline_snapshot["cache_stale"],
            pending_events=offline_snapshot["pending_events"],
            replay_ready=replay_ready,
            backlog_threshold=self.config.pending_backlog_threshold,
        )

        backpressure = self.offline_state.backpressure_profile(
            threshold=self.config.pending_backlog_threshold,
            hard_limit=self.config.pending_backlog_hard_limit,
        )
        cache_window = self.offline_state.cache_window(
            self.config.offline_cache_ttl_seconds, offline_snapshot.get("last_cache_flush")
        )

        capability_report = self.offline_state.capability_report(
            self.config.offline_cache_dir,
            self.config.offline_cache_ttl_seconds,
            offline_snapshot.get("cached_events", 0),
            offline_snapshot.get("cache_stale", False),
            offline_snapshot.get("last_cache_flush"),
        )
        offline_snapshot.update({
            "capability_report": capability_report,
            "capability_readiness": capability_report.get("capability_snapshot", {}).get("readiness"),
            "capability_posture": capability_report.get("capability_snapshot", {}).get("posture"),
            "capability_gaps": capability_report.get("capability_snapshot", {}).get("disabled"),
            "backpressure": backpressure,
            "cache_window": cache_window,
        })

        resilience = {
            "grade": offline_snapshot.get("resilience_grade"),
            "score": offline_snapshot.get("resilience_score"),
            "summary": offline_snapshot.get("resilience_summary"),
            "next_action": self._recommend_next_action(offline_snapshot),
        }
        offline_snapshot["recommended_action"] = resilience["next_action"]

        payload = {
            "online": offline_snapshot["online"],
            "last_sync": offline_snapshot["last_sync"],
            "metrics": metrics.__dict__,
            "offline": offline_snapshot,
            "resilience": resilience,
        }
        self.event_bus.emit("device_status", payload)
        payload["events"] = self.event_bus.stats()
        return payload

    def handle_task(self, task: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        decision = self.router.route(task, payload)
        response = {"task": task, "target": decision.target, "payload": payload or {}, "fallback": decision.fallback_used}
        self.event_bus.emit("task_executed", response)
        return response

    def export_offline_state(self, destination: Optional[Path] = None) -> Path:
        package_path = destination or (self.config.offline_cache_dir / "offline_package.json")
        return self.offline_state.export_offline_package(
            self.config.offline_cache_dir,
            package_path,
            cache_ttl_seconds=self.config.offline_cache_ttl_seconds,
        )

    def flush_events(self) -> None:
        self.offline_state.prune_stale_cache(
            self.config.offline_cache_dir, self.config.offline_cache_ttl_seconds
        )
        if self.offline_state.online:
            cached_events = self.offline_state.restore_cache(self.config.offline_cache_dir)
            self.offline_state.pending_events.clear()
            new_events = [event.to_dict() for event in self.event_bus.history[self._last_flush_index :]]

            self._write_events(cached_events + new_events)
            self._last_flush_index = len(self.event_bus.history)
            self.offline_state.last_sync = datetime.now(timezone.utc).isoformat()
        else:
            self.offline_state.flush_to_cache(self.config.offline_cache_dir)
            self._last_flush_index = len(self.event_bus.history)

    def safe_run_shell(self, command: str, args: Optional[list[str]] = None) -> Dict[str, Any]:
        result = self.broker.run_shell(command, args)
        return json.loads(result.to_json())

    def safe_get_sensor(self, name: str) -> Dict[str, Any]:
        return self.broker.get_sensor(name)

    def safe_read_file(self, path: Path) -> str:
        return self.broker.read_file(path)

    def safe_write_config(self, path: Path, content: Dict[str, str]) -> None:
        self.broker.write_config(path, content)

    def _recommend_next_action(self, offline_snapshot: Dict[str, Any]) -> str:
        backlog = offline_snapshot.get("pending_events", 0)
        backlog_threshold = self.config.pending_backlog_threshold
        cache_stale = bool(offline_snapshot.get("cache_stale"))
        cache_present = self.config.offline_cache_dir.exists()
        offline_reason = offline_snapshot.get("offline_reason")

        if cache_stale:
            return "Cache marked stale; refresh offline cache or trigger sync to rebuild manifest."
        if backlog > backlog_threshold:
            return (
                f"Pending event backlog {backlog} exceeds guardrail {backlog_threshold}; "
                "flush events when connectivity is available."
            )
        if not cache_present:
            return "Create offline cache directory to retain audit trail before next run."
        if not offline_snapshot.get("online", False):
            reason = offline_reason or "connectivity unavailable"
            return f"Operating offline ({reason}); prepare offline package for replay."
        return "Posture steady; continue periodic heartbeats and capability checks."

    def _write_events(self, events: list[dict]) -> None:
        if not events:
            return

        self.config.event_log.parent.mkdir(parents=True, exist_ok=True)
        with self.config.event_log.open("a", encoding="utf-8") as handle:
            for payload in events:
                handle.write(json.dumps(payload) + "\n")


__all__ = ["OuterLinkRuntime"]


def main() -> None:
    runtime = OuterLinkRuntime()
    runtime.emit_state()
    runtime.flush_events()


if __name__ == "__main__":
    main()
