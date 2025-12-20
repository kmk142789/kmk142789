from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .abilities import AbilityRegistry, default_outerlink_abilities
from .broker import ExecutionBroker
from .dsi import DeviceSurfaceInterface
from .events import EventBus
from .router import TaskRouter
from .sources import ExternalSourceRegistry
from .utils import OfflineState, SafeModeConfig


class OuterLinkRuntime:
    """Offline-first coordinator that binds router, broker, and event system."""

    def __init__(self, config: Optional[SafeModeConfig] = None, offline_state: Optional[OfflineState] = None) -> None:
        self.config = config or SafeModeConfig.from_env()
        self.offline_state = offline_state or OfflineState()
        self.event_bus = EventBus(max_history=self.config.event_history_limit)
        self.dsi = DeviceSurfaceInterface(self.config)
        self.broker = ExecutionBroker(self.config, self.dsi, self.event_bus, self.offline_state)
        self.router = TaskRouter(
            self.event_bus,
            self.offline_state,
            backlog_threshold=self.config.pending_backlog_threshold,
            backlog_hard_limit=self.config.pending_backlog_hard_limit,
        )
        self.abilities = AbilityRegistry(default_outerlink_abilities())
        self.sources = ExternalSourceRegistry()
        self._last_flush_index = 0
        self._bootstrap_default_mappings()
        self._bootstrap_sources()

    def _bootstrap_default_mappings(self) -> None:
        self.router.register_module("device_status", "dsi")
        self.router.register_module("optimization_tick", "optimizer")
        self.router.register_module("policy_eval", "governance")

    def _bootstrap_sources(self) -> None:
        self.sources.load_from(self.config.external_source_manifest)
        if not self.sources.list_sources():
            self.sources.register_from_payloads(
                [
                    {
                        "source_id": "outerlink_authority",
                        "title": "OuterLink System Definition",
                        "url": "outerlink/OUTERLINK_SYSTEM_DEFINITION.md",
                        "classification": "authoritative",
                        "description": "Offline-first runtime specification for OuterLink.",
                    }
                ]
            )

    def emit_state(self) -> Dict[str, Any]:
        metrics = self.dsi.get_metrics()
        self.offline_state.enforce_backpressure(self.config.pending_backlog_hard_limit)
        offline_snapshot, resilience = self.offline_state.analyze_offline_posture(
            self.config.offline_cache_dir,
            self.config.offline_cache_ttl_seconds,
            self.config.pending_backlog_threshold,
            self.config.pending_backlog_hard_limit,
        )
        self.abilities.sync_from_capabilities(offline_snapshot.get("capabilities", {}))

        health_report = self.offline_state.write_health_report(
            self.config.offline_cache_dir,
            self.config.offline_cache_dir / "offline_health.json",
            self.config.offline_cache_ttl_seconds,
            self.config.pending_backlog_threshold,
        )

        source_bundle = self.sources.build_citation_bundle(
            online=bool(offline_snapshot.get("online")),
            offline_reason=offline_snapshot.get("offline_reason"),
            ttl_seconds=self.config.external_source_ttl_seconds,
        )
        source_artifact_path = self.sources.write_artifact(
            self.config.offline_cache_dir / self.config.source_artifact_name,
            source_bundle,
        )
        self._sync_source_capabilities(source_bundle, source_artifact_path)
        refreshed_snapshot = self.offline_state.status(
            self.config.offline_cache_dir,
            self.config.offline_cache_ttl_seconds,
        )
        offline_snapshot.update(
            {
                "capabilities": refreshed_snapshot.get("capabilities"),
                "capability_history": refreshed_snapshot.get("capability_history"),
                "capability_readiness": refreshed_snapshot.get("capability_readiness"),
                "capability_posture": refreshed_snapshot.get("capability_posture"),
                "capability_gaps": refreshed_snapshot.get("capability_gaps"),
                "capability_report": refreshed_snapshot.get("capability_report"),
            }
        )
        self.abilities.sync_from_capabilities(offline_snapshot.get("capabilities", {}), source="source_bundle")

        payload = {
            "online": offline_snapshot["online"],
            "last_sync": offline_snapshot["last_sync"],
            "metrics": metrics.__dict__,
            "offline": offline_snapshot,
            "resilience": resilience,
            "digest": self.offline_state.posture_digest(offline_snapshot, resilience),
            "health_report": str(health_report),
            "abilities": self.abilities.snapshot(),
            "sources": source_bundle,
            "source_artifact": str(source_artifact_path),
        }
        self.event_bus.emit("device_status", payload)
        payload["events"] = self.event_bus.stats()
        return payload

    def handle_task(self, task: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        decision = self.router.route(task, payload)
        response = {
            "task": task,
            "target": decision.target,
            "payload": payload or {},
            "fallback": decision.fallback_used,
            "reason": decision.reason,
        }
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
        stats = self.event_bus.stats()
        total_events = stats.get("total") or len(self.event_bus.history)
        dropped_events = stats.get("dropped") or 0
        start_index = max(0, self._last_flush_index - dropped_events)

        if self.offline_state.online:
            cached_events = self.offline_state.restore_cache(self.config.offline_cache_dir)
            self.offline_state.pending_events.clear()
            new_events = [
                event.to_dict() for event in self.event_bus.history_since(start_index)
            ]

            self._write_events(cached_events + new_events)
            self._last_flush_index = total_events
            self.offline_state.last_sync = datetime.now(timezone.utc).isoformat()
        else:
            self.offline_state.flush_to_cache(self.config.offline_cache_dir)
            self._last_flush_index = total_events

    def safe_run_shell(self, command: str, args: Optional[list[str]] = None) -> Dict[str, Any]:
        result = self.broker.run_shell(command, args)
        return json.loads(result.to_json())

    def safe_get_sensor(self, name: str) -> Dict[str, Any]:
        return self.broker.get_sensor(name)

    def safe_read_file(self, path: Path) -> str:
        return self.broker.read_file(path)

    def safe_write_config(self, path: Path, content: Dict[str, str]) -> None:
        self.broker.write_config(path, content)

    def ingest_neural_link(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Accept NeuralLink payloads and emit them as OuterLink events."""

        envelope = {
            "event": "neural_link_pulse",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        self.event_bus.emit("neural_link_pulse", envelope)
        if not self.offline_state.online:
            self.offline_state.record_pending(envelope)
        return envelope

    def _sync_source_capabilities(self, source_bundle: Dict[str, Any], source_artifact: Path) -> None:
        citations = source_bundle.get("citations", [])
        online = bool(source_bundle.get("online"))
        has_placeholders = any(citation.get("placeholder") for citation in citations)
        has_uncertainty = any(citation.get("uncertainty") for citation in citations)
        has_classification = bool(source_bundle.get("classification_summary"))
        has_updates = bool(source_bundle.get("update_summary"))

        self.offline_state.set_capability("structured_citations", True, note="Citation bundle generated")
        self.offline_state.set_capability("source_classification", has_classification)
        self.offline_state.set_capability("update_awareness", has_updates)
        self.offline_state.set_capability("offline_uncertainty_marking", has_uncertainty)
        self.offline_state.set_capability("placeholder_references", has_placeholders)
        self.offline_state.set_capability("source_artifacts", source_artifact.exists())

        if not online and not has_uncertainty:
            self.offline_state.add_resilience_note(
                "Offline citations produced without uncertainty markers; verify placeholder policy"
            )

    def _recommend_next_action(self, offline_snapshot: Dict[str, Any]) -> str:
        plan = self.offline_state.resilience_action_plan(
            cache_present=self.config.offline_cache_dir.exists(),
            cache_stale=bool(offline_snapshot.get("cache_stale")),
            backlog=int(offline_snapshot.get("pending_events", 0)),
            backlog_threshold=self.config.pending_backlog_threshold,
            offline_reason=offline_snapshot.get("offline_reason"),
            online=bool(offline_snapshot.get("online")),
            manifest_valid=bool(offline_snapshot.get("manifest_valid", True)),
        )
        return plan.get("next_action", "Posture steady; continue periodic heartbeats and capability checks.")

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
