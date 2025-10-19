"""Echo Harmonix SDK helpers for orchestrating bridge sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from cognitive_harmonics.harmonix_bridge import (
    BridgeConfig,
    BridgeNode,
    BridgeTuning,
    DistributedBridgeGraph,
    EchoBridgeHarmonix,
    PolicyEngine,
    PolicyProgram,
    SecureChannelSpec,
)
from .bridge_emitter import BridgeEmitter


@dataclass(slots=True)
class EchoBridgeSession:
    """Lightweight session facade returned by :func:`connect`."""

    harmonix: EchoBridgeHarmonix

    def run_cycle(self) -> Dict[str, object]:
        state, payload = self.harmonix.run_cycle()
        return {
            "state": state,
            "payload": payload,
            "telemetry": dict(state.telemetry),
            "mesh": state.mesh.mesh_snapshot(),
            "policy": {
                "actions": list(state.last_policy_actions),
                "results": list(state.last_policy_results),
            },
        }

    def mesh_snapshot(self) -> Dict[str, object]:
        return self.harmonix.state.mesh.mesh_snapshot()

    def policy_actions(self) -> Dict[str, object]:
        return {
            "actions": list(self.harmonix.state.last_policy_actions),
            "results": list(self.harmonix.state.last_policy_results),
        }


def _build_policy_engine(policy: PolicyEngine | PolicyProgram | str | None) -> PolicyEngine:
    return PolicyEngine.from_policy(policy)


def connect(
    endpoint: str,
    policy: PolicyEngine | PolicyProgram | str | None = None,
    *,
    tuning: Optional[BridgeTuning] = None,
    secure_protocol: str = "quic",
    config: Optional[BridgeConfig] = None,
) -> EchoBridgeSession:
    """Create an :class:`EchoBridgeSession` bound to the Harmonix orchestrator."""

    emitter = BridgeEmitter(config) if config is not None else None
    controller = DistributedBridgeGraph(controller_id=f"harmonix@{endpoint}")
    channel_template = SecureChannelSpec(protocol=secure_protocol)
    policy_engine = _build_policy_engine(policy)

    harmonix = EchoBridgeHarmonix(
        emitter=emitter,
        tuning=tuning,
        mesh_controller=controller,
        policy=policy_engine,
        secure_channel=channel_template,
    )

    controller.register_node(
        BridgeNode(
            node_id="bridge-0",
            endpoint=endpoint,
            region="core",
            status="active",
            secure_channel=channel_template.spawn("bridge-0", harmonix.state.tuning.token),
        )
    )

    return EchoBridgeSession(harmonix=harmonix)


harmonix_connect = connect


__all__ = [
    "EchoBridgeSession",
    "connect",
    "harmonix_connect",
]

