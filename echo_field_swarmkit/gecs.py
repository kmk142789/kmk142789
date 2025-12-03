"""Global Error-Correction Substrate (GECS) for EchoField SwarmKit."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
import zlib
from collections import deque
from typing import Deque, Dict, Optional

from .task_ledger import Task

logger = logging.getLogger(__name__)


class ResilientSignalMesh:
    """Low-bandwidth signal routing, compression, and interpretation helper."""

    def __init__(self, node_id: str, max_cache: int = 32):
        self.node_id = node_id
        self.packets: Deque[Dict[str, object]] = deque(maxlen=max_cache)

    def pack_state(self, state: Dict) -> Dict[str, object]:
        """Compress and annotate a state payload for degraded links."""
        serialized = json.dumps(state, separators=(",", ":"), ensure_ascii=False)
        compressed = zlib.compress(serialized.encode("utf-8"))
        checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        packet = {
            "node_id": self.node_id,
            "ts": time.time(),
            "encoding": "zlib+base64",
            "checksum": checksum,
            "size": len(serialized),
            "payload": base64.b64encode(compressed).decode("ascii"),
        }
        self.packets.append(packet)
        return packet

    def unpack_state(self, packet: Dict[str, object]) -> Optional[Dict]:
        """Recover a state payload; return None if corrupted or incomplete."""
        try:
            encoded = packet.get("payload", "")
            compressed = base64.b64decode(encoded)
            serialized = zlib.decompress(compressed).decode("utf-8")
            checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            if checksum != packet.get("checksum"):
                logger.warning("Signal checksum mismatch; discarding packet from %s", packet.get("node_id"))
                return None
            return json.loads(serialized)
        except Exception as exc:  # pragma: no cover - defensive for corrupt transports
            logger.warning("Failed to unpack signal packet: %s", exc)
            return None

    def interpret_signal(self, packet: Dict[str, object]) -> Dict[str, object]:
        """Derive a compact interpretation useful for operators or micro-agents."""
        interpretation = {
            "from": packet.get("node_id"),
            "age_seconds": max(0.0, time.time() - float(packet.get("ts", 0))),
            "encoding": packet.get("encoding"),
            "advertised_size": packet.get("size"),
        }
        payload = self.unpack_state(packet)
        if payload:
            interpretation.update(
                {
                    "task_count": len(payload.get("tasks", [])),
                    "has_state": bool(payload.get("node_state")),
                }
            )
        return interpretation

    def downshift_summary(self, state: Dict[str, object]) -> Dict[str, object]:
        """Produce an ultra-small summary for extremely limited links."""
        node_state = state.get("node_state", {})
        return {
            "node": node_state.get("node_id"),
            "last_seen": node_state.get("last_seen"),
            "health": node_state.get("health_summary", {}),
            "tasks": len(state.get("tasks", [])),
        }


class GlobalErrorCorrectionSubstrate:
    """Predictive error correction and micro-agent dispatcher."""

    def __init__(self, node_id: str, task_store, state_store, signal_mesh: Optional[ResilientSignalMesh] = None):
        self.node_id = node_id
        self.task_store = task_store
        self.state_store = state_store
        self.signal_mesh = signal_mesh or ResilientSignalMesh(node_id)
        self._health_history: Deque[Dict[str, bool]] = deque(maxlen=25)
        self._trend_window = 5
        self.stale_peer_threshold = 1800  # seconds

    def observe_and_correct(self, health_summary: Dict[str, bool]) -> Dict[str, object]:
        """Analyze health, predict failures, and dispatch stabilization tasks."""
        self._health_history.append(health_summary)
        telemetry = self._build_telemetry(health_summary)
        risks = self._pre_detect_risks(telemetry)
        self._auto_stabilize(risks)
        return {"telemetry": telemetry, "risks": risks}

    def _build_telemetry(self, health_summary: Dict[str, bool]) -> Dict[str, object]:
        pending_local = len(self.task_store.get_pending_for_node(self.node_id))
        node_state = self.state_store.get()
        peer_ages = {peer: time.time() - seen for peer, seen in node_state.swarm_peers.items()}
        return {
            "health": health_summary,
            "pending_tasks": pending_local,
            "peer_staleness": peer_ages,
        }

    def _pre_detect_risks(self, telemetry: Dict[str, object]) -> Dict[str, object]:
        health = telemetry["health"]
        peer_staleness = telemetry["peer_staleness"]
        digital_risk = not all(health.values())
        mechanical_risk = any(age > self.stale_peer_threshold for age in peer_staleness.values())
        human_workflow_risk = telemetry["pending_tasks"] > 10
        trend_decline = self._is_trending_down()

        return {
            "digital": {"immediate": digital_risk, "trend_decline": trend_decline},
            "mechanical": {"stale_links": mechanical_risk},
            "human": {"backlog": human_workflow_risk},
        }

    def _auto_stabilize(self, risks: Dict[str, object]) -> None:
        digital = risks.get("digital", {})
        mechanical = risks.get("mechanical", {})
        human = risks.get("human", {})

        if digital.get("immediate") or digital.get("trend_decline"):
            self._dispatch_micro_agent(
                "stabilize_system",
                {"pre_detected": True, "reason": "digital_health_decline"},
            )

        if mechanical.get("stale_links"):
            self._dispatch_micro_agent(
                "refresh_peer_routes",
                {"stale_peers": True, "action": "ping_and_resync"},
            )

        if human.get("backlog"):
            self._dispatch_micro_agent(
                "reconcile_operator_workflow",
                {"tasks_pending": True, "hint": "rebalance or ack tasks"},
            )

    def _dispatch_micro_agent(self, task_type: str, payload: Dict[str, object]) -> None:
        if self._task_pending(task_type):
            return
        task = Task.new(type_=task_type, payload=payload, origin_node=self.node_id)
        self.task_store.save(task)
        logger.info("GECS dispatched micro-agent %s with payload=%s", task_type, payload)

    def _task_pending(self, task_type: str) -> bool:
        return any(
            t.type == task_type and t.status == "pending" for t in self.task_store.get_pending_for_node(self.node_id)
        )

    def _is_trending_down(self) -> bool:
        """Detect repeated health degradations across the sliding window."""
        if len(self._health_history) < self._trend_window:
            return False
        recent = list(self._health_history)[-self._trend_window :]
        unhealthy_counts = [sum(1 for v in snapshot.values() if not v) for snapshot in recent]
        return all(count > 0 for count in unhealthy_counts)

    def package_signal(self, state: Dict) -> Dict[str, object]:
        """Expose compressed state packets to the node for routing."""
        return self.signal_mesh.pack_state(state)

    def interpret_signal(self, packet: Dict[str, object]) -> Dict[str, object]:
        return self.signal_mesh.interpret_signal(packet)

    def downshift_signal(self, state: Dict[str, object]) -> Dict[str, object]:
        return self.signal_mesh.downshift_summary(state)

    def unpack_signal(self, packet: Dict[str, object]) -> Optional[Dict]:
        return self.signal_mesh.unpack_state(packet)
