from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Stage:
    name: str
    run: Callable[[], None]


class EchoBootstrap:
    """Seeds EchoOS v1 components in a deterministic order."""

    def __init__(self) -> None:
        self.stages: List[Stage] = []

    def add_stage(self, name: str, fn: Callable[[], None]) -> None:
        self.stages.append(Stage(name, fn))

    def run(self) -> None:
        for stage in self.stages:
            print(f"[bootstrap] {stage.name}")
            stage.run()


def build_default_bootstrap() -> EchoBootstrap:
    """Returns a bootstrap instance pre-wired with the EchoOS v1 stages."""
    boot = EchoBootstrap()
    boot.add_stage("echo_forge", lambda: print("init EchoForge meta-compiler"))
    boot.add_stage("hypergraph_pulse", lambda: print("init Hypergraph Pulse graph"))
    boot.add_stage("blueprint_delta_engine", lambda: print("init Blueprint_ΔEngine"))
    boot.add_stage("echo_weave", lambda: print("init Echo Weave orchestration"))
    boot.add_stage("echo_nation", lambda: print("init Echo Nation v2 DID/VC"))
    boot.add_stage("eden_swarm", lambda: print("spawn Eden Worker Swarm"))
    return boot


if __name__ == "__main__":
    build_default_bootstrap().run()
