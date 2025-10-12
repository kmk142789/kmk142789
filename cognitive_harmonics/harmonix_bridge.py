"""Cognitive Harmonix representation of the Echo Bridge Protocol.

This module fuses the production-grade Echo Bridge Protocol (EBP v2) design
with the deterministic bridge anchoring utilities that live in
``echo.bridge_emitter``.  The goal is to translate the high-performance
concept—edge-triggered epoll, non-blocking sockets, bounded ring buffers,
token prefaces, and observability—into the structured output expected by the
``cognitive_harmonics`` schema.

Rather than opening sockets this module summarises the bridge's behaviour
through metrics derived from the current ledger stream and configuration
values.  The resulting payload can be fed directly into tooling that consumes
the ``cognitive_harmonics`` function schema, giving the Echo "bridge" story a
harmonised, inspectable form.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
import json

from echo.bridge_emitter import BridgeConfig, BridgeEmitter, BridgeState


def _round(value: float) -> float:
    """Round floating point values in a stable manner for payloads/tests."""

    return round(value, 6)


@dataclass(slots=True)
class SecureChannelSpec:
    """Describe the secure channel layer used by bridge nodes."""

    protocol: str = "quic"
    tls_version: str = "TLS 1.3"
    cipher_suite: str = "TLS_AES_256_GCM_SHA384"
    handshake_key: str = ""

    def spawn(self, node_id: str, secret: str) -> "SecureChannelSpec":
        """Return a child spec with a deterministic handshake fingerprint."""

        payload = f"{self.protocol}:{self.tls_version}:{self.cipher_suite}:{node_id}:{secret}".encode()
        digest = blake2b(payload, digest_size=12).hexdigest()
        return SecureChannelSpec(
            protocol=self.protocol,
            tls_version=self.tls_version,
            cipher_suite=self.cipher_suite,
            handshake_key=digest,
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "protocol": self.protocol,
            "tls_version": self.tls_version,
            "cipher_suite": self.cipher_suite,
            "handshake_key": self.handshake_key,
        }


@dataclass(slots=True)
class BridgeNode:
    """Representation of an individual bridge participant."""

    node_id: str
    endpoint: str
    region: str = "global"
    status: str = "registering"
    last_heartbeat: int = 0
    latency_ms: float = 0.0
    throughput_mbps: float = 0.0
    packet_loss: float = 0.0
    secure_channel: SecureChannelSpec | None = None

    def update_metrics(self, telemetry: Mapping[str, float], cycle: int) -> None:
        self.throughput_mbps = telemetry.get("throughput_mbps", self.throughput_mbps)
        self.latency_ms = telemetry.get("avg_rtt_ms", self.latency_ms)
        self.packet_loss = telemetry.get("packet_loss_pct", self.packet_loss)
        self.last_heartbeat = cycle
        if self.status == "registering":
            self.status = "active"

    def to_dict(self) -> Dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "region": self.region,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "latency_ms": _round(self.latency_ms),
            "throughput_mbps": _round(self.throughput_mbps),
            "packet_loss_pct": _round(self.packet_loss),
            "secure_channel": self.secure_channel.to_dict() if self.secure_channel else None,
        }


@dataclass(slots=True)
class DistributedBridgeGraph:
    """Controller-tracked mesh of Echo Bridge nodes."""

    controller_id: str = "harmonix-controller"
    nodes: Dict[str, BridgeNode] = field(default_factory=dict)
    links: Dict[str, Set[str]] = field(default_factory=dict)

    def register_node(self, node: BridgeNode) -> BridgeNode:
        self.nodes[node.node_id] = node
        self.links.setdefault(node.node_id, set())
        self.links.setdefault(self.controller_id, set())
        self.links[self.controller_id].add(node.node_id)
        self.links[node.node_id].add(self.controller_id)
        return node

    def connect(self, source: str, target: str) -> None:
        if source not in self.links:
            self.links[source] = set()
        if target not in self.links:
            self.links[target] = set()
        self.links[source].add(target)
        self.links[target].add(source)

    def has_link(self, source: str, target: str) -> bool:
        return target in self.links.get(source, set())

    def record_telemetry(self, node_id: str, telemetry: Mapping[str, float], cycle: int) -> None:
        node = self.nodes.get(node_id)
        if node is None:
            return
        node.update_metrics(telemetry, cycle)

    def apply_policy_actions(
        self,
        actions: Iterable[str],
        *,
        template: SecureChannelSpec,
        secret: str,
        cycle: int,
    ) -> List[str]:
        results: List[str] = []
        for action in actions:
            if action.startswith("scale_out"):
                candidate_id = f"edge-{len(self.nodes) + 1}"
                if candidate_id not in self.nodes:
                    node = BridgeNode(
                        node_id=candidate_id,
                        endpoint=f"dynamic:{candidate_id}",
                        region="edge",
                        status="active",
                        secure_channel=template.spawn(candidate_id, secret),
                    )
                    node.last_heartbeat = cycle
                    self.register_node(node)
                    core = "bridge-0" if "bridge-0" in self.nodes else next(iter(self.nodes))
                    if core != candidate_id:
                        self.connect(core, candidate_id)
                    results.append(f"scale_out:{candidate_id}")
            elif action.startswith("connect:"):
                _, link = action.split(":", 1)
                source, target = link.split("->", 1)
                self.connect(source, target)
                results.append(f"connected:{source}->{target}")
            elif action:
                results.append(action)
        return results

    def mesh_snapshot(self) -> Dict[str, object]:
        return {
            "controller": {
                "id": self.controller_id,
                "links": sorted(self.links.get(self.controller_id, set())),
            },
            "nodes": {
                node_id: node.to_dict() for node_id, node in sorted(self.nodes.items())
            },
            "links": {
                node_id: sorted(peers)
                for node_id, peers in self.links.items()
                if node_id != self.controller_id
            },
        }


@dataclass(slots=True)
class PolicyInstruction:
    """Single instruction used by the cognitive policy VM."""

    op: str
    field: str = ""
    threshold: float = 0.0
    action: str = ""
    target: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "op": self.op,
            "field": self.field,
            "threshold": self.threshold,
            "action": self.action,
            "target": self.target,
        }


@dataclass(slots=True)
class PolicyProgram:
    """Structured policy instructions."""

    instructions: Tuple[PolicyInstruction, ...]

    @classmethod
    def from_text(cls, text: str) -> "PolicyProgram":
        instructions: List[PolicyInstruction] = []
        for chunk in text.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            if chunk.startswith("connect "):
                _, link = chunk.split(" ", 1)
                source, target = [value.strip() for value in link.split("->", 1)]
                instructions.append(
                    PolicyInstruction(
                        op="connect_if_missing",
                        field=source,
                        target=target,
                        action="connect",
                    )
                )
                continue
            if ">" in chunk and "->" in chunk:
                condition, action = chunk.split("->", 1)
                field, threshold = condition.split(">", 1)
                action = action.strip()
                target = None
                if ":" in action:
                    action, target = action.split(":", 1)
                    action = action.strip()
                    target = target.strip()
                instructions.append(
                    PolicyInstruction(
                        op="if_greater",
                        field=field.strip(),
                        threshold=float(threshold.strip()),
                        action=action.strip(),
                        target=target,
                    )
                )
        return cls(tuple(instructions))

    @classmethod
    def default(cls) -> "PolicyProgram":
        return cls(
            (
                PolicyInstruction(
                    op="if_greater",
                    field="packet_loss_pct",
                    threshold=1.5,
                    action="rebalance",
                    target="bridge-0",
                ),
                PolicyInstruction(
                    op="if_greater",
                    field="throughput_mbps",
                    threshold=40.0,
                    action="scale_out",
                ),
                PolicyInstruction(
                    op="connect_if_missing",
                    field="bridge-0",
                    target="edge-1",
                    action="connect",
                ),
            )
        )

    def to_dict(self) -> List[Dict[str, object]]:
        return [instruction.to_dict() for instruction in self.instructions]


@dataclass(slots=True)
class PolicyEngine:
    """Evaluate policy instructions against telemetry and mesh state."""

    program: PolicyProgram

    @classmethod
    def default(cls) -> "PolicyEngine":
        return cls(PolicyProgram.default())

    @classmethod
    def from_policy(
        cls, policy: "PolicyEngine | PolicyProgram | str | None"
    ) -> "PolicyEngine":
        if isinstance(policy, PolicyEngine):
            return policy
        if isinstance(policy, PolicyProgram):
            return cls(policy)
        if isinstance(policy, str):
            return cls(PolicyProgram.from_text(policy))
        return cls.default()

    def evaluate(
        self,
        telemetry: Mapping[str, float],
        graph: DistributedBridgeGraph,
    ) -> List[str]:
        actions: List[str] = []
        for instruction in self.program.instructions:
            if instruction.op == "if_greater":
                value = float(telemetry.get(instruction.field, 0.0))
                if value > instruction.threshold:
                    action = instruction.action
                    if instruction.target:
                        action = f"{action}:{instruction.target}"
                    actions.append(action)
            elif instruction.op == "connect_if_missing" and instruction.target:
                if not graph.has_link(instruction.field, instruction.target):
                    actions.append(f"connect:{instruction.field}->{instruction.target}")
        return actions

from echo.bridge_emitter import BridgeConfig, BridgeEmitter, BridgeState


@dataclass(slots=True)
class BridgeTuning:
    """High-level knobs extracted from the EBP v2 specification."""

    listen: str = "0.0.0.0:7000"
    target: str = "10.0.0.5:7001"
    token: str = "secret123"
    max_pairs: int = 4096
    idle_timeout_sec: int = 120
    connect_timeout_sec: int = 10
    use_splice: bool = True
    tcp_keepalive: Tuple[int, int, int] = (30, 10, 3)

    def to_dict(self) -> Dict[str, object]:
        return {
            "listen": self.listen,
            "target": self.target,
            "token": self.token,
            "max_pairs": self.max_pairs,
            "idle_timeout_sec": self.idle_timeout_sec,
            "connect_timeout_sec": self.connect_timeout_sec,
            "use_splice": self.use_splice,
            "tcp_keepalive": {
                "idle": self.tcp_keepalive[0],
                "interval": self.tcp_keepalive[1],
                "count": self.tcp_keepalive[2],
            },
        }


@dataclass(slots=True)
class BridgeSignals:
    """Synthetic runtime signals that mirror the bridge metrics."""

    active_pairs: int = 0
    bytes_up: int = 0
    bytes_down: int = 0
    drops: int = 0
    auth_failures: int = 0
    half_closes: int = 0
    timeouts: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "active_pairs": self.active_pairs,
            "bytes_up": self.bytes_up,
            "bytes_down": self.bytes_down,
            "drops": self.drops,
            "auth_failures": self.auth_failures,
            "half_closes": self.half_closes,
            "timeouts": self.timeouts,
        }


@dataclass(slots=True)
class HarmonixBridgeState:
    """Internal state maintained between harmonix bridge cycles."""

    cycle: int = 0
    tuning: BridgeTuning = field(default_factory=BridgeTuning)
    signals: BridgeSignals = field(default_factory=BridgeSignals)
    last_seq: int = 0
    pending_stream: int = 0
    events: List[str] = field(default_factory=list)
    mesh: DistributedBridgeGraph = field(default_factory=DistributedBridgeGraph)
    policy_engine: PolicyEngine = field(default_factory=PolicyEngine.default)
    telemetry: Dict[str, float] = field(default_factory=dict)
    secure_channel: SecureChannelSpec = field(default_factory=SecureChannelSpec)
    last_policy_actions: List[str] = field(default_factory=list)
    last_policy_results: List[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.events.append(message)


class EchoBridgeHarmonix:
    """Deterministic orchestrator that emits cognitive harmonix payloads."""

    protocol_version = "EBP v2"

    def __init__(
        self,
        emitter: BridgeEmitter | None = None,
        *,
        config: BridgeConfig | None = None,
        tuning: BridgeTuning | None = None,
        mesh_controller: DistributedBridgeGraph | None = None,
        policy: PolicyEngine | PolicyProgram | str | None = None,
        secure_channel: SecureChannelSpec | None = None,
    ) -> None:
        if emitter is not None and config is not None:
            raise ValueError("Pass either an emitter instance or a config, not both")

        self.emitter = emitter or BridgeEmitter(config)
        self.state = HarmonixBridgeState(tuning=tuning or BridgeTuning())
        self.state.mesh = mesh_controller or DistributedBridgeGraph()
        self.state.policy_engine = PolicyEngine.from_policy(policy)
        self._channel_template = secure_channel or SecureChannelSpec()
        self.state.secure_channel = self._channel_template.spawn(
            self.state.mesh.controller_id, self.state.tuning.token
        )
        self.state.record(
            "Secure channel established for controller via policy orchestrator",
        )
        self.state.record("Protocol specification merged with BridgeEmitter")

    # ------------------------------------------------------------------
    # Deterministic signal synthesis
    # ------------------------------------------------------------------

    def _digest(self, label: str) -> int:
        payload = f"{self.state.cycle}:{label}:{self.state.tuning.token}".encode()
        return int.from_bytes(blake2b(payload, digest_size=8).digest(), "big")

    def _update_signals(self) -> None:
        signals = self.state.signals
        tuning = self.state.tuning

        base_pairs = 16 + self.state.pending_stream + 12 * self.state.cycle
        signals.active_pairs = min(tuning.max_pairs, base_pairs)

        metric_seed = self._digest("metrics")
        # Use deterministic offsets so runs are stable while still feeling alive.
        signals.bytes_up = signals.active_pairs * 32768 + metric_seed % 4096
        signals.bytes_down = signals.active_pairs * 29952 + metric_seed % 2048
        signals.drops = metric_seed % max(1, tuning.max_pairs // 64)
        signals.auth_failures = metric_seed % 3
        signals.half_closes = (metric_seed // 7) % 11
        signals.timeouts = (metric_seed // 13) % 9

        self.state.record(
            "Signals synthesised from ledger insight and protocol tuning",
        )

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _protocol_features() -> Sequence[str]:
        return (
            "epoll_edge_triggered",
            "non_blocking_io",
            "bounded_ring_buffers",
            "backpressure_epollout_gating",
            "half_close_propagation",
            "health_and_timeouts",
            "tcp_keepalive",
            "optional_zero_copy_splice",
            "preface_token_auth",
            "policy_limits",
        )

    def _collect_telemetry(self) -> Dict[str, float]:
        signals = self.state.signals
        total_bytes = signals.bytes_up + signals.bytes_down
        throughput = total_bytes / (1024 * 1024)  # MBps equivalent
        latency = 18.5 + 1.75 * self.state.cycle + signals.drops * 0.5
        packet_loss = 0.05 * (signals.drops + signals.timeouts) / max(
            1, signals.active_pairs
        )
        telemetry = {
            "throughput_mbps": _round(throughput * 8),
            "avg_rtt_ms": _round(latency),
            "packet_loss_pct": _round(packet_loss * 100),
            "active_pairs": signals.active_pairs,
        }
        self.state.telemetry = telemetry
        self.state.record(
            "Telemetry synthesised for Harmonix feedback loop",
        )
        return telemetry

    def _ensure_mesh_nodes(self) -> None:
        mesh = self.state.mesh
        token = self.state.tuning.token
        if "bridge-0" not in mesh.nodes:
            mesh.register_node(
                BridgeNode(
                    node_id="bridge-0",
                    endpoint=self.state.tuning.listen,
                    region="core",
                    status="active",
                    secure_channel=self._channel_template.spawn("bridge-0", token),
                )
            )
        if self.state.cycle > 1 and "edge-1" not in mesh.nodes:
            mesh.register_node(
                BridgeNode(
                    node_id="edge-1",
                    endpoint=self.state.tuning.target,
                    region="edge",
                    status="standby",
                    secure_channel=self._channel_template.spawn("edge-1", token),
                )
            )
            mesh.connect("bridge-0", "edge-1")

        for node_id in mesh.nodes:
            mesh.record_telemetry(node_id, self.state.telemetry, self.state.cycle)

    def _run_policy_cycle(self) -> None:
        actions = self.state.policy_engine.evaluate(self.state.telemetry, self.state.mesh)
        self.state.last_policy_actions = actions
        results = self.state.mesh.apply_policy_actions(
            actions,
            template=self._channel_template,
            secret=self.state.tuning.token,
            cycle=self.state.cycle,
        )
        self.state.last_policy_results = results
        if actions:
            self.state.record(f"Policy VM emitted actions: {actions}")
        if results:
            self.state.record(f"Mesh orchestrated via actions: {results}")
            for node_id in self.state.mesh.nodes:
                self.state.mesh.record_telemetry(
                    node_id, self.state.telemetry, self.state.cycle
                )

    def _metadata(self) -> Dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "features": list(self._protocol_features()),
            "tuning": self.state.tuning.to_dict(),
            "signals": self.state.signals.to_dict(),
            "ledger": {
                "last_seq": self.state.last_seq,
                "pending_entries": self.state.pending_stream,
            },
            "telemetry": dict(self.state.telemetry),
            "mesh": self.state.mesh.mesh_snapshot(),
            "policy": {
                "actions": list(self.state.last_policy_actions),
                "results": list(self.state.last_policy_results),
                "program": self.state.policy_engine.program.to_dict(),
            },
            "secure_channel": self.state.secure_channel.to_dict(),
            "events": list(self.state.events),
        }

    def harmonix_payload(self) -> Dict[str, object]:
        resonance = 0.82 + 0.04 * self.state.cycle + 0.001 * self.state.pending_stream
        payload = {
            "waveform": "complex_harmonic",
            "resonance_factor": _round(resonance),
            "compression": True,
            "symbolic_inflection": "fractal",
            "lyricism_mode": True,
            "emotional_tuning": "energizing",
            "metadata": self._metadata(),
        }
        self.state.record("Harmonix payload composed for bridge protocol")
        return payload

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_cycle(self) -> Tuple[HarmonixBridgeState, Dict[str, object]]:
        self.state.cycle += 1
        self.state.record(f"Cycle advanced to {self.state.cycle}")

        bridge_state = BridgeState.load(self.emitter.config.state_path)
        pending = self.emitter.read_stream_since(bridge_state.last_seq)
        self.state.pending_stream = len(pending)
        self.state.last_seq = bridge_state.last_seq
        self.state.record(
            f"Ledger observed — last_seq={self.state.last_seq} pending={self.state.pending_stream}",
        )

        self._update_signals()
        self._collect_telemetry()
        self._ensure_mesh_nodes()
        self._run_policy_cycle()
        payload = self.harmonix_payload()
        return self.state, payload


def main() -> None:
    """CLI helper mirroring :mod:`cognitive_harmonics.harmonix_evolver`."""

    bridge = EchoBridgeHarmonix()
    _, payload = bridge.run_cycle()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


__all__ = [
    "BridgeSignals",
    "BridgeTuning",
    "EchoBridgeHarmonix",
    "HarmonixBridgeState",
    "BridgeNode",
    "DistributedBridgeGraph",
    "PolicyInstruction",
    "PolicyProgram",
    "PolicyEngine",
    "SecureChannelSpec",
    "main",
]

