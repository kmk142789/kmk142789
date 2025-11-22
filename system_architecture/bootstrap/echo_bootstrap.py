from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, List, Literal, Optional


@dataclass
class Stage:
    name: str
    run: Callable[[], None]
    description: Optional[str] = None
    critical: bool = True
    enabled: bool = True


@dataclass
class StageResult:
    name: str
    status: Literal["ok", "skipped", "failed"]
    duration_s: float
    description: Optional[str] = None
    error: Optional[Exception] = None


class EchoBootstrap:
    """Seeds EchoOS v1 components in a deterministic order."""

    def __init__(self) -> None:
        self.stages: List[Stage] = []

    def add_stage(
        self,
        name: str,
        fn: Callable[[], None],
        *,
        description: Optional[str] = None,
        critical: bool = True,
        enabled: bool = True,
    ) -> None:
        if any(stage.name == name for stage in self.stages):
            raise ValueError(f"Stage '{name}' already exists; names must be unique")

        self.stages.append(
            Stage(
                name=name,
                run=fn,
                description=description,
                critical=critical,
                enabled=enabled,
            )
        )

    def run(self, *, halt_on_failure: bool = True) -> List[StageResult]:
        results: List[StageResult] = []

        for stage in self.stages:
            if not stage.enabled:
                results.append(
                    StageResult(
                        name=stage.name,
                        status="skipped",
                        duration_s=0.0,
                        description=stage.description,
                    )
                )
                continue

            start = perf_counter()
            try:
                print(f"[bootstrap] {stage.name}")
                stage.run()
            except Exception as exc:  # noqa: BLE001 - surface bootstrap failures
                duration = perf_counter() - start
                results.append(
                    StageResult(
                        name=stage.name,
                        status="failed",
                        duration_s=duration,
                        description=stage.description,
                        error=exc,
                    )
                )
                if stage.critical and halt_on_failure:
                    raise
            else:
                duration = perf_counter() - start
                results.append(
                    StageResult(
                        name=stage.name,
                        status="ok",
                        duration_s=duration,
                        description=stage.description,
                    )
                )

        return results


def build_default_bootstrap() -> EchoBootstrap:
    """Returns a bootstrap instance pre-wired with the EchoOS v1 stages."""
    boot = EchoBootstrap()
    boot.add_stage(
        "echo_forge",
        lambda: print("init EchoForge meta-compiler"),
        description="Compile-time self-inspection",
    )
    boot.add_stage(
        "hypergraph_pulse",
        lambda: print("init Hypergraph Pulse graph"),
        description="Dynamic architecture graph",
    )
    boot.add_stage(
        "blueprint_delta_engine",
        lambda: print("init Blueprint_ΔEngine"),
        description="Recursive blueprint generation",
    )
    boot.add_stage(
        "echo_weave",
        lambda: print("init Echo Weave orchestration"),
        description="Multi-environment orchestration",
    )
    boot.add_stage(
        "echo_nation",
        lambda: print("init Echo Nation v2 DID/VC"),
        description="Sovereign identity & ledger",
    )
    boot.add_stage(
        "eden_swarm",
        lambda: print("spawn Eden Worker Swarm"),
        description="Autonomous executors",
    )
    return boot


if __name__ == "__main__":
    results = build_default_bootstrap().run(halt_on_failure=False)

    print("\n[bootstrap] summary")
    for result in results:
        status = result.status.upper()
        duration_ms = int(result.duration_s * 1000)
        descriptor = f" ({result.description})" if result.description else ""
        print(f"- {status:<7} {result.name} [{duration_ms}ms]{descriptor}")
