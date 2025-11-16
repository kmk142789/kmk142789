"""Central coordinator for the Echo Genesis Core.

The :class:`EchoGenesisCoordinator` acts as the connective tissue between the
:class:`~echo.echo_genesis_core.EchoGenesisCore` synthesis engine and the
individual subsystem surfaces that power Echo.  It ensures that each subsystem
is registered with a probe, tracks the latest state for dashboards, and
constructs an interaction mesh so orchestration layers can reason about how
signals influence each other.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Sequence
import json

from .echo_genesis_core import EchoGenesisCore, SubsystemProbe, self_or_dict

ExtractorFn = Callable[[Any], Mapping[str, Any] | MutableMapping[str, Any] | Any]


@dataclass(slots=True)
class SubsystemLink:
    """Descriptor defining how a subsystem is connected to the coordinator."""

    name: str
    kind: str
    focus: str
    provider: Any
    extractor: ExtractorFn
    weight: float
    dependencies: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class EchoGenesisCoordinator:
    """Central state manager that keeps subsystem interactions coherent."""

    def __init__(
        self,
        genesis_core: EchoGenesisCore,
        *,
        state_dir: Path | str | None = None,
        history_limit: int = 64,
    ) -> None:
        self.genesis_core = genesis_core
        self._links: dict[str, SubsystemLink] = {}
        self._subsystem_state: dict[str, Mapping[str, Any]] = {}
        self._history: deque[Mapping[str, Any]] = deque(maxlen=max(8, int(history_limit)))
        self._state_dir = Path(state_dir or "state/echo_genesis_coordinator")
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._snapshot_path = self._state_dir / "coordinator_state.json"
        self._history_path = self._state_dir / "coordinator_history.jsonl"
        self._latest_cycle: Mapping[str, Any] | None = None

    # ------------------------------------------------------------------
    # Subsystem wiring
    # ------------------------------------------------------------------
    def link_subsystem(
        self,
        name: str,
        provider: Any,
        *,
        kind: str,
        focus: str,
        extractor: ExtractorFn | None = None,
        weight: float = 1.0,
        dependencies: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> SubsystemProbe:
        """Register ``provider`` with the Genesis Core and track its state."""

        if name in self._links:
            raise ValueError(f"subsystem '{name}' already linked")
        extractor = extractor or self._default_extractor
        link = SubsystemLink(
            name=name,
            kind=kind,
            focus=focus,
            provider=provider,
            extractor=extractor,
            weight=weight,
            dependencies=tuple(dependencies or ()),
            tags=tuple(tags or ()),
            metadata=dict(metadata or {}),
        )

        def _probe(link: SubsystemLink = link) -> Mapping[str, Any]:
            payload = link.extractor(link.provider)
            normalized = self._enrich_with_dependencies(link.name, payload, link.dependencies)
            self._subsystem_state[link.name] = normalized
            return normalized

        probe = SubsystemProbe(
            name=name,
            kind=kind,
            focus=focus,
            probe=_probe,
            weight=weight,
            tags=link.tags,
        )
        self.genesis_core.register_probe(probe)
        self._links[name] = link
        return probe

    # ------------------------------------------------------------------
    # Coordination loop
    # ------------------------------------------------------------------
    def cycle(self) -> Mapping[str, Any]:
        """Run a synthesis cycle and persist the unified coordinator state."""

        architecture = self.genesis_core.synthesize()
        mesh = self._interaction_mesh()
        coordination_index = self._coordination_index(mesh, architecture)
        composite = {
            "generated_at": architecture["generated_at"],
            "architecture": architecture,
            "subsystems": self._subsystems_snapshot(),
            "interaction_mesh": mesh,
            "coordination_index": coordination_index,
            "latest_path": str(self._snapshot_path),
            "history_path": str(self._history_path),
        }
        history_entry = {
            "generated_at": composite["generated_at"],
            "coordination_index": coordination_index,
            "refinement_index": architecture["refinement_index"],
        }
        self._history.append(history_entry)
        self._persist(composite, history_entry)
        self._latest_cycle = composite
        return composite

    def snapshot(self) -> Mapping[str, Any]:
        """Return a lightweight snapshot for dashboards and CLIs."""

        latest = self._latest_cycle or self._load_latest()
        payload = {
            "generated_at": self._now_iso(),
            "latest_cycle": latest,
            "links": {
                name: {
                    "kind": link.kind,
                    "focus": link.focus,
                    "dependencies": list(link.dependencies),
                    "metadata": dict(link.metadata),
                    "tags": list(link.tags),
                }
                for name, link in sorted(self._links.items())
            },
            "history": list(self._history),
            "state_path": str(self._snapshot_path),
            "history_path": str(self._history_path),
        }
        return payload

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _subsystems_snapshot(self) -> Mapping[str, Any]:
        return {
            name: {
                "kind": link.kind,
                "focus": link.focus,
                "dependencies": list(link.dependencies),
                "metadata": dict(link.metadata),
                "state": self._subsystem_state.get(name, {}),
            }
            for name, link in sorted(self._links.items())
        }

    def _interaction_mesh(self) -> Mapping[str, Any]:
        edges: list[Mapping[str, Any]] = []
        for source, link in self._links.items():
            for target in link.dependencies:
                if target in self._links:
                    edges.append({"source": source, "target": target})
        nodes = len(self._links)
        possible_edges = max(1, nodes * (nodes - 1))
        density = round(len(edges) / possible_edges, 4)
        return {"edges": edges, "density": density, "nodes": nodes}

    def _coordination_index(
        self,
        mesh: Mapping[str, Any],
        architecture: Mapping[str, Any],
    ) -> float:
        subsystems = architecture.get("architecture", {}).get("subsystems", {})
        if not subsystems:
            return 0.0
        signals = [float(payload.get("signal", 0.0)) for payload in subsystems.values()]
        mean_signal = sum(signals) / len(signals)
        density = float(mesh.get("density", 0.0))
        score = mean_signal * 0.7 + density * 0.3
        return round(max(0.0, min(1.0, score)), 4)

    def _enrich_with_dependencies(
        self,
        name: str,
        payload: Mapping[str, Any] | MutableMapping[str, Any] | Any,
        dependencies: Sequence[str],
    ) -> Mapping[str, Any]:
        normalized = self._normalize_payload(payload)
        if dependencies:
            linked_state = {
                dep: self._subsystem_state.get(dep)
                for dep in dependencies
                if dep in self._subsystem_state
            }
            linked_state = {k: v for k, v in linked_state.items() if v is not None}
            if linked_state:
                enriched = dict(normalized)
                enriched["linked_state"] = linked_state
                return enriched
        return normalized

    def _normalize_payload(
        self, payload: Mapping[str, Any] | MutableMapping[str, Any] | Any
    ) -> Mapping[str, Any]:
        if payload is None:
            return {}
        if isinstance(payload, Mapping):
            return dict(payload)
        normalized = self_or_dict(payload)
        if isinstance(normalized, Mapping):
            return dict(normalized)
        return {"value": normalized}

    def _default_extractor(self, provider: Any) -> Mapping[str, Any]:
        candidates = ("snapshot", "state", "summary", "to_dict")
        for attr in candidates:
            if hasattr(provider, attr):
                value = getattr(provider, attr)
                if callable(value):
                    try:
                        return self._normalize_payload(value())
                    except Exception:  # pragma: no cover - defensive path
                        continue
                return self._normalize_payload(value)
        if callable(provider):
            return self._normalize_payload(provider())
        return self._normalize_payload(provider)

    def _persist(self, payload: Mapping[str, Any], history_entry: Mapping[str, Any]) -> None:
        with self._snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        with self._history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(history_entry, ensure_ascii=False) + "\n")
        self._trim_history()

    def _load_latest(self) -> Mapping[str, Any] | None:
        if not self._snapshot_path.exists():
            return None
        try:
            with self._snapshot_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:  # pragma: no cover - corrupted state guard
            return None

    def _trim_history(self) -> None:
        if not self._history_path.exists():
            return
        lines = self._history_path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= self._history.maxlen:
            return
        trimmed = "\n".join(lines[-self._history.maxlen :]) + "\n"
        self._history_path.write_text(trimmed, encoding="utf-8")

    @property
    def state_path(self) -> Path:
        return self._snapshot_path

    @property
    def history_path(self) -> Path:
        return self._history_path

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ["EchoGenesisCoordinator", "SubsystemLink"]
