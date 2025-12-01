from __future__ import annotations

"""BridgeLink: cross-AI syncing glue between mesh, shell, Eden88, and horizon agents."""

from dataclasses import dataclass
from typing import Iterable, List, Optional

from outerlink import OuterLinkMeshNetwork

from .echo_shell_runtime_loop import EchoShellRuntimeLoop
from .eden88_autonomous_thread import Eden88AutonomousThread
from multi_agent_horizon_engine import MultiAgentHorizonEngine


@dataclass
class BridgeSnapshot:
    mesh_health: dict
    shell_uptime: float
    eden_history: List[dict]
    horizon_bridge: str
    synthesized_probability: float
    last_commands: List[str]


class BridgeLink:
    """Synchronizes state across the mesh, EchoShell, Eden88, and horizon agents."""

    def __init__(
        self,
        mesh: OuterLinkMeshNetwork,
        shell_loop: EchoShellRuntimeLoop,
        eden_thread: Eden88AutonomousThread,
        horizon: MultiAgentHorizonEngine,
    ) -> None:
        self.mesh = mesh
        self.shell_loop = shell_loop
        self.eden_thread = eden_thread
        self.horizon = horizon

    def sync(self, commands: Optional[Iterable[str]] = None) -> BridgeSnapshot:
        commands_list = list(commands or [])
        if commands_list:
            self.shell_loop.run_commands(commands_list)
        mesh_health = self.mesh.aggregate_health()
        horizon_reports = self.horizon.run()
        synthesized_probability = self.horizon.synthesize_probability(horizon_reports)
        bridge_summary = self.horizon.render_bridge(horizon_reports)
        return BridgeSnapshot(
            mesh_health=mesh_health,
            shell_uptime=self.shell_loop.uptime_seconds,
            eden_history=self.eden_thread.history,
            horizon_bridge=bridge_summary,
            synthesized_probability=synthesized_probability,
            last_commands=commands_list,
        )

    def start(self) -> None:
        self.shell_loop.start()
        self.eden_thread.start()

    def stop(self) -> None:
        self.shell_loop.stop()
        self.eden_thread.stop()
