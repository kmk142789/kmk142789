"""Self-organizing coordination core for Echo subsystems."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

ObserveFn = Callable[[], Mapping[str, Any] | MutableMapping[str, Any]]
EvolveFn = Callable[[Mapping[str, Any]], Mapping[str, Any] | None]


@dataclass(slots=True)
class SubsystemAdapter:
    """Adapter describing how to interface with a subsystem."""

    name: str
    kind: str
    intent: str
    observe: ObserveFn
    evolve: EvolveFn | None = None
    priority: float = 1.0


@dataclass(slots=True)
class SubsystemSnapshot:
    """Snapshot captured from a subsystem during coordination."""

    name: str
    kind: str
    intent: str
    signal: float
    status: str
    telemetry: Mapping[str, Any]
    priority: float
    recommendations: list[str] = field(default_factory=list)
    momentum: float = 0.0


@dataclass(slots=True)
class SelfOrganizingPlan:
    """Structured plan emitted after a coordination pass."""

    generated_at: str
    autonomy_score: float
    subsystems: list[SubsystemSnapshot]
    network: Mapping[str, Any]
    priorities: list[Mapping[str, Any]]
    momentum: Mapping[str, Any]


class SelfOrganizingCore:
    """Coordinate and evolve Echo subsystems using adaptive heuristics."""

    def __init__(
        self,
        *,
        subsystems: Sequence[SubsystemAdapter],
        state_dir: Path | str | None = None,
    ) -> None:
        if not subsystems:
            raise ValueError("at least one subsystem is required")
        self._subsystems = list(subsystems)
        self._state_dir = Path(state_dir or "state/self_organizing_core")
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._plan_path = self._state_dir / "plan_latest.json"
        self._history_path = self._state_dir / "plan_history.jsonl"

    @property
    def subsystems(self) -> tuple[SubsystemAdapter, ...]:
        """Return the registered subsystem adapters."""

        return tuple(self._subsystems)

    def register_subsystem(self, adapter: SubsystemAdapter) -> None:
        """Register an additional subsystem at runtime."""

        self._subsystems.append(adapter)

    def coordinate(self) -> SelfOrganizingPlan:
        """Collect subsystem telemetry and emit a new plan."""

        previous = self._load_previous_plan()
        snapshots = [self._introspect(adapter, previous) for adapter in self._subsystems]
        network = self._build_network(snapshots)
        priorities = self._rank_priorities(snapshots)
        momentum = self._system_momentum(previous, snapshots)
        autonomy = self._autonomy_score(snapshots)
        plan = SelfOrganizingPlan(
            generated_at=self._now_iso(),
            autonomy_score=autonomy,
            subsystems=snapshots,
            network=network,
            priorities=priorities,
            momentum=momentum,
        )
        self._persist_plan(plan)
        return plan

    def _introspect(
        self,
        adapter: SubsystemAdapter,
        previous: Mapping[str, Any] | None,
    ) -> SubsystemSnapshot:
        try:
            payload = adapter.observe() or {}
            telemetry = dict(payload)
            error: str | None = None
        except Exception as exc:  # pragma: no cover - defensive guard
            telemetry = {"status": "error", "detail": str(exc)}
            error = str(exc)
        signal = self._derive_signal(telemetry)
        status = self._status_from_signal(signal)
        recommendations = self._recommendations(telemetry, signal, adapter.intent)
        snapshot = SubsystemSnapshot(
            name=adapter.name,
            kind=adapter.kind,
            intent=adapter.intent,
            signal=signal,
            status="degraded" if error else status,
            telemetry=telemetry,
            priority=adapter.priority,
            recommendations=recommendations,
            momentum=self._subsystem_momentum(previous, adapter.name, signal),
        )
        if adapter.evolve:
            evolution_payload = {
                "status": snapshot.status,
                "signal": snapshot.signal,
                "recommendations": snapshot.recommendations,
                "telemetry": snapshot.telemetry,
            }
            try:
                adapter.evolve(evolution_payload)
            except Exception:
                snapshot.recommendations.append("evolution_handler_failed")
        return snapshot

    def _derive_signal(self, telemetry: Mapping[str, Any]) -> float:
        progress = self._extract_float(telemetry, ("progress", "completion", "ratio"))
        coherence = self._extract_float(telemetry, ("coherence", "score", "confidence"))
        vitality = self._extract_float(telemetry, ("vitality", "energy", "intensity"))
        samples = [value for value in (progress, coherence, vitality) if value is not None]
        if not samples:
            return 0.25
        return round(sum(samples) / len(samples), 4)

    def _status_from_signal(self, signal: float) -> str:
        if signal >= 0.8:
            return "thriving"
        if signal >= 0.55:
            return "stabilizing"
        if signal >= 0.35:
            return "incubating"
        return "dormant"

    def _recommendations(
        self,
        telemetry: Mapping[str, Any],
        signal: float,
        intent: str,
    ) -> list[str]:
        actions: list[str] = []
        if signal < 0.35:
            actions.append(f"amplify {intent}")
        elif signal < 0.55:
            actions.append(f"stabilize {intent}")
        else:
            actions.append(f"sustain {intent}")
        if telemetry.get("issues"):
            actions.append("resolve issues")
        if telemetry.get("next_step"):
            actions.append("advance next_step")
        return actions

    def _subsystem_momentum(
        self,
        previous: Mapping[str, Any] | None,
        name: str,
        signal: float,
    ) -> float:
        if not previous:
            return 0.0
        prev_subsystems = previous.get("subsystems")
        if not isinstance(prev_subsystems, Iterable):
            return 0.0
        for payload in prev_subsystems:
            if not isinstance(payload, Mapping):
                continue
            if payload.get("name") == name:
                prev_signal = self._extract_float(payload, ("signal",))
                if prev_signal is None:
                    return 0.0
                return round(signal - prev_signal, 4)
        return 0.0

    def _system_momentum(
        self,
        previous: Mapping[str, Any] | None,
        snapshots: Sequence[SubsystemSnapshot],
    ) -> Mapping[str, Any]:
        delta = sum(snapshot.momentum for snapshot in snapshots)
        trend = "accelerating" if delta > 0 else "regressing" if delta < 0 else "steady"
        return {"delta": round(delta, 4), "trend": trend}

    def _build_network(self, snapshots: Sequence[SubsystemSnapshot]) -> Mapping[str, Any]:
        nodes = [
            {
                "id": snapshot.name,
                "kind": snapshot.kind,
                "intent": snapshot.intent,
                "signal": snapshot.signal,
                "status": snapshot.status,
            }
            for snapshot in snapshots
        ]
        edges = []
        for i, first in enumerate(snapshots):
            for second in snapshots[i + 1 :]:
                weight = round((first.signal + second.signal) / 2.0, 4)
                edges.append(
                    {
                        "source": first.name,
                        "target": second.name,
                        "weight": weight,
                        "relationship": self._relationship(first, second),
                    }
                )
        return {"nodes": nodes, "edges": edges}

    def _relationship(
        self,
        first: SubsystemSnapshot,
        second: SubsystemSnapshot,
    ) -> str:
        if first.intent == second.intent:
            return "harmonic"
        if first.kind == second.kind:
            return "parallel"
        return "synergistic"

    def _rank_priorities(self, snapshots: Sequence[SubsystemSnapshot]) -> list[Mapping[str, Any]]:
        ranked = sorted(
            snapshots,
            key=lambda snap: (snap.signal * 0.7 + snap.priority * 0.3),
            reverse=True,
        )
        return [
            {
                "name": snap.name,
                "status": snap.status,
                "signal": snap.signal,
                "priority": snap.priority,
                "recommendations": list(snap.recommendations),
            }
            for snap in ranked
        ]

    def _autonomy_score(self, snapshots: Sequence[SubsystemSnapshot]) -> float:
        signal = sum(snapshot.signal for snapshot in snapshots)
        scope = len(snapshots)
        if scope == 0:
            return 0.0
        return round(min(1.0, (signal / scope) * 0.9 + 0.1), 4)

    def _persist_plan(self, plan: SelfOrganizingPlan) -> None:
        payload = {
            "generated_at": plan.generated_at,
            "autonomy_score": plan.autonomy_score,
            "subsystems": [asdict(snapshot) for snapshot in plan.subsystems],
            "network": plan.network,
            "priorities": plan.priorities,
            "momentum": plan.momentum,
        }
        with self._plan_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        with self._history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _load_previous_plan(self) -> Mapping[str, Any] | None:
        if not self._plan_path.exists():
            return None
        try:
            with self._plan_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_float(
        payload: Mapping[str, Any],
        keys: Iterable[str],
    ) -> float | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, (float, int)):
                return float(value)
        return None

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def from_components(
        cls,
        *,
        evolver: "EchoEvolver" | None = None,
        orchestrator: "OrchestratorCore" | None = None,
        loop: "SelfSustainingLoop" | None = None,
        pulsenet: "PulseNetGatewayService" | None = None,
        bridge: "BridgeSyncService" | None = None,
        state_dir: Path | str | None = None,
    ) -> "SelfOrganizingCore":
        adapters: list[SubsystemAdapter] = []
        if evolver is not None:
            adapters.append(
                SubsystemAdapter(
                    name="EchoEvolver",
                    kind="evolver",
                    intent="cycle",
                    observe=lambda: evolver.cycle_digest(persist_artifact=False),
                    priority=0.9,
                )
            )
        if orchestrator is not None:
            adapters.append(
                SubsystemAdapter(
                    name="Orchestrator",
                    kind="orchestrator",
                    intent="coordination",
                    observe=lambda: orchestrator.latest_decision or orchestrator.orchestrate(),
                    priority=0.95,
                )
            )
        if loop is not None:
            adapters.append(
                SubsystemAdapter(
                    name="SelfSustainingLoop",
                    kind="governance",
                    intent="governance",
                    observe=lambda: dict(getattr(loop, "state", {})),
                    priority=0.7,
                )
            )
        if pulsenet is not None:
            adapters.append(
                SubsystemAdapter(
                    name="PulseNet",
                    kind="telemetry",
                    intent="signal",
                    observe=lambda: {
                        "summary": pulsenet.pulse_summary(),
                        "attestations": pulsenet.latest_attestations(limit=5),
                        "registrations": list(
                            pulsenet.registrations() if hasattr(pulsenet, "registrations") else []
                        ),
                    },
                    priority=0.8,
                )
            )
        if bridge is not None:
            adapters.append(
                SubsystemAdapter(
                    name="EchoBridge",
                    kind="bridge",
                    intent="sync",
                    observe=lambda: {
                        "connectors": getattr(bridge, "connectors", []),
                        "log_path": str(getattr(bridge, "log_path", "")),
                    },
                    priority=0.6,
                )
            )
        return cls(subsystems=adapters, state_dir=state_dir)


__all__ = [
    "SelfOrganizingCore",
    "SelfOrganizingPlan",
    "SubsystemAdapter",
    "SubsystemSnapshot",
]
