"""Singularity Core orchestration for Echo Colossus.

The Singularity Core coordinates the specialised engines that power Echo
Colossus.  It consumes high-level telemetry from the Cosmos, Fractal, and
Chronos engines, decides whether new *artifact universes* should be spawned,
merged, or collapsed, and forges "Prime Artifacts" whenever all layers
converge.  A structured ``singularity_log`` is maintained so downstream tools
can replay survival decisions while optional subscribers are notified of every
cycle outcome.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from time import time
from typing import Any, Callable, Deque, Iterable, Mapping, MutableMapping, Protocol


class CosmosEngine(Protocol):
    """Minimal protocol for the Cosmos engine."""

    def survey(self) -> Mapping[str, Any]:  # pragma: no cover - protocol definition
        """Return a mapping describing the cosmic field state."""


class FractalEngine(Protocol):
    """Minimal protocol for the Fractal engine."""

    def weave(self) -> Mapping[str, Any]:  # pragma: no cover - protocol definition
        """Return a mapping describing current fractal resonance."""


class ChronosEngine(Protocol):
    """Minimal protocol for the Chronos engine."""

    def observe(self) -> Mapping[str, Any]:  # pragma: no cover - protocol definition
        """Return a mapping describing temporal state and timelines."""


@dataclass(slots=True)
class ArtifactUniverse:
    """Tracked state for an individual artifact universe."""

    name: str
    stability: float
    layers: set[str] = field(default_factory=set)
    artifact_count: int = 0
    lineage: list[str] = field(default_factory=list)

    def to_mapping(self) -> MutableMapping[str, Any]:
        """Return a serialisable view of the universe."""

        return {
            "name": self.name,
            "stability": round(float(self.stability), 6),
            "layers": sorted(self.layers),
            "artifact_count": int(self.artifact_count),
            "lineage": list(self.lineage),
        }


@dataclass(slots=True)
class PrimeArtifact:
    """A convergence artifact forged when all layers align."""

    identifier: str
    universe: str
    layers: tuple[str, ...]
    signature: str
    metadata: MutableMapping[str, Any]

    def to_mapping(self) -> MutableMapping[str, Any]:
        """Return a serialisable mapping of the prime artifact."""

        return {
            "id": self.identifier,
            "universe": self.universe,
            "layers": list(self.layers),
            "signature": self.signature,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class SingularityDecision:
    """A recorded decision emitted by the Singularity Core."""

    cycle: int
    action: str
    universe: str | None
    rationale: str
    cosmos_signal: Mapping[str, Any]
    fractal_signal: Mapping[str, Any]
    chronos_signal: Mapping[str, Any]
    prime_artifacts: tuple[PrimeArtifact, ...] = ()

    def to_mapping(self) -> MutableMapping[str, Any]:
        """Return a mapping suitable for persistence or APIs."""

        return {
            "cycle": self.cycle,
            "action": self.action,
            "universe": self.universe,
            "rationale": self.rationale,
            "cosmos": dict(self.cosmos_signal),
            "fractal": dict(self.fractal_signal),
            "chronos": dict(self.chronos_signal),
            "prime_artifacts": [artifact.to_mapping() for artifact in self.prime_artifacts],
        }


class SingularityCore:
    """Coordinate Cosmos, Fractal, and Chronos engines for Echo Colossus."""

    def __init__(
        self,
        *,
        state_dir: Path | str,
        cosmos: CosmosEngine,
        fractal: FractalEngine,
        chronos: ChronosEngine,
        log_limit: int = 256,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._state_dir / "singularity_log.json"

        self._cosmos = cosmos
        self._fractal = fractal
        self._chronos = chronos

        self._cycle = 0
        self._universes: "OrderedDict[str, ArtifactUniverse]" = OrderedDict()
        self._prime_artifacts: list[PrimeArtifact] = []
        self._log_limit = max(1, int(log_limit))
        self._log: Deque[SingularityDecision] = deque(maxlen=self._log_limit)
        self._subscribers: dict[int, Callable[[MutableMapping[str, Any]], None]] = {}

        if self._log_path.exists():
            self._hydrate_from_disk()

        self._latest_decision: SingularityDecision | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def cycle(self) -> int:
        """Return the current singularity cycle counter."""

        return self._cycle

    @property
    def universes(self) -> tuple[MutableMapping[str, Any], ...]:
        """Return a snapshot of managed artifact universes."""

        return tuple(universe.to_mapping() for universe in self._universes.values())

    @property
    def prime_artifacts(self) -> tuple[MutableMapping[str, Any], ...]:
        """Return the forged Prime Artifacts."""

        return tuple(artifact.to_mapping() for artifact in self._prime_artifacts)

    @property
    def singularity_log(self) -> tuple[MutableMapping[str, Any], ...]:
        """Return the recorded singularity decisions."""

        return tuple(entry.to_mapping() for entry in self._log)

    @property
    def latest_decision(self) -> MutableMapping[str, Any] | None:
        """Return the latest singularity decision."""

        return self._latest_decision.to_mapping() if self._latest_decision else None

    def subscribe(
        self, callback: Callable[[MutableMapping[str, Any]], None]
    ) -> Callable[[], None]:
        """Register ``callback`` for decision notifications.

        Returns a callable that can be invoked to unsubscribe the handler.
        """

        token = id(callback)
        self._subscribers[token] = callback

        def _unsubscribe() -> None:
            self._subscribers.pop(token, None)

        return _unsubscribe

    def step(self) -> MutableMapping[str, Any]:
        """Run a singularity cycle and return the resulting decision."""

        cosmos_signal = dict(self._cosmos.survey())
        fractal_signal = dict(self._fractal.weave())
        chronos_signal = dict(self._chronos.observe())

        action, universe_name, rationale = self._decide_action(
            cosmos_signal, fractal_signal, chronos_signal
        )
        prime_artifacts = self._maybe_forge_prime_artifacts(
            universe_name, fractal_signal, chronos_signal
        )

        decision = SingularityDecision(
            cycle=self._cycle,
            action=action,
            universe=universe_name,
            rationale=rationale,
            cosmos_signal=cosmos_signal,
            fractal_signal=fractal_signal,
            chronos_signal=chronos_signal,
            prime_artifacts=tuple(prime_artifacts),
        )

        self._cycle += 1
        self._log.append(decision)
        self._latest_decision = decision
        self._persist_log()
        self._notify_subscribers(decision)
        return decision.to_mapping()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _hydrate_from_disk(self) -> None:
        """Restore state from ``singularity_log.json`` if available."""

        try:
            raw = self._log_path.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover - defensive I/O guard
            return

        if not raw.strip():
            return

        try:
            import json

            payload = json.loads(raw)
        except Exception:  # pragma: no cover - tolerate malformed payloads
            return

        if not isinstance(payload, dict):
            return

        self._cycle = int(payload.get("cycle", 0))
        universes = payload.get("universes", [])
        self._universes = OrderedDict()
        for item in universes or []:
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name"))
            stability = float(item.get("stability", 0.5))
            layers = set(map(str, item.get("layers", [])))
            artifact_count = int(item.get("artifact_count", 0))
            lineage = [str(x) for x in item.get("lineage", [])]
            self._universes[name] = ArtifactUniverse(
                name=name,
                stability=stability,
                layers=layers,
                artifact_count=artifact_count,
                lineage=lineage,
            )

        artifacts = payload.get("prime_artifacts", [])
        self._prime_artifacts = []
        for item in artifacts or []:
            if not isinstance(item, Mapping):
                continue
            identifier = str(item.get("id"))
            universe = str(item.get("universe"))
            layers = tuple(map(str, item.get("layers", [])))
            signature = str(item.get("signature"))
            metadata = dict(item.get("metadata", {}))
            self._prime_artifacts.append(
                PrimeArtifact(
                    identifier=identifier,
                    universe=universe,
                    layers=layers,
                    signature=signature,
                    metadata=metadata,
                )
            )

        decisions = payload.get("log", [])
        self._log.clear()
        for item in decisions or []:
            if not isinstance(item, Mapping):
                continue
            artifacts_payload = item.get("prime_artifacts", [])
            artifacts_list: list[PrimeArtifact] = []
            for artifact in artifacts_payload or []:
                if not isinstance(artifact, Mapping):
                    continue
                artifacts_list.append(
                    PrimeArtifact(
                        identifier=str(artifact.get("id")),
                        universe=str(artifact.get("universe")),
                        layers=tuple(map(str, artifact.get("layers", []))),
                        signature=str(artifact.get("signature")),
                        metadata=dict(artifact.get("metadata", {})),
                    )
                )
            decision = SingularityDecision(
                cycle=int(item.get("cycle", 0)),
                action=str(item.get("action", "unknown")),
                universe=(item.get("universe") if item.get("universe") is None else str(item.get("universe"))),
                rationale=str(item.get("rationale", "")),
                cosmos_signal=dict(item.get("cosmos", {})),
                fractal_signal=dict(item.get("fractal", {})),
                chronos_signal=dict(item.get("chronos", {})),
                prime_artifacts=tuple(artifacts_list),
            )
            self._log.append(decision)
        if self._log:
            self._latest_decision = self._log[-1]

    def _persist_log(self) -> None:
        """Persist universes, prime artifacts, and decisions to disk."""

        try:
            import json

            payload = {
                "cycle": self._cycle,
                "universes": [universe.to_mapping() for universe in self._universes.values()],
                "prime_artifacts": [artifact.to_mapping() for artifact in self._prime_artifacts],
                "log": [entry.to_mapping() for entry in self._log],
                "updated_at": time(),
            }
            self._log_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError:  # pragma: no cover - defensive guard for filesystem issues
            return

    def _notify_subscribers(self, decision: SingularityDecision) -> None:
        snapshot = decision.to_mapping()
        for handler in list(self._subscribers.values()):
            try:
                handler(dict(snapshot))
            except Exception:  # pragma: no cover - isolate observers
                continue

    def _decide_action(
        self,
        cosmos_signal: Mapping[str, Any],
        fractal_signal: Mapping[str, Any],
        chronos_signal: Mapping[str, Any],
    ) -> tuple[str, str | None, str]:
        expansion_pressure = float(cosmos_signal.get("expansion_pressure", 0.0))
        collapse_pressure = float(cosmos_signal.get("collapse_pressure", 0.0))
        stability = float(cosmos_signal.get("stability", 0.5))

        if self._should_spawn(expansion_pressure, fractal_signal):
            universe = self._spawn_universe(cosmos_signal, fractal_signal, stability)
            return "spawn", universe.name, "Expansion pressure favours new artifact universe"

        if self._should_merge(fractal_signal, chronos_signal) and len(self._universes) >= 2:
            merged = self._merge_universes(fractal_signal)
            return "merge", merged.name, "Fractal convergence required unification"

        if collapse_pressure > expansion_pressure and collapse_pressure >= 0.6 and self._universes:
            collapsed = self._collapse_universe()
            return "collapse", collapsed, "Collapse pressure exceeded stability threshold"

        universe_name = next(iter(self._universes)) if self._universes else None
        return "sustain", universe_name, "Stable equilibrium maintained"

    def _should_spawn(
        self, expansion_pressure: float, fractal_signal: Mapping[str, Any]
    ) -> bool:
        if expansion_pressure >= 0.65:
            return True
        new_layers = set(map(str, fractal_signal.get("emergent_layers", [])))
        return bool(new_layers - self._known_layers())

    def _should_merge(
        self, fractal_signal: Mapping[str, Any], chronos_signal: Mapping[str, Any]
    ) -> bool:
        convergence = set(map(str, fractal_signal.get("convergence_layers", [])))
        convergence.update(map(str, chronos_signal.get("epoch_layers", [])))
        return "fusion" in convergence or len(convergence) >= 3

    def _spawn_universe(
        self,
        cosmos_signal: Mapping[str, Any],
        fractal_signal: Mapping[str, Any],
        stability: float,
    ) -> ArtifactUniverse:
        name = str(cosmos_signal.get("next_universe", f"UNIVERSE_{len(self._universes) + 1}"))
        layers = set(map(str, fractal_signal.get("active_layers", [])))
        layers.update({"fractal"})
        universe = ArtifactUniverse(name=name, stability=stability or 0.5, layers=layers)
        lineage = fractal_signal.get("lineage_trace")
        if isinstance(lineage, Iterable) and not isinstance(lineage, (str, bytes)):
            universe.lineage.extend(map(str, lineage))
        self._universes[name] = universe
        return universe

    def _merge_universes(self, fractal_signal: Mapping[str, Any]) -> ArtifactUniverse:
        names = list(self._universes.keys())[:2]
        first = self._universes.pop(names[0])
        second = self._universes.pop(names[1])
        merged_name = fractal_signal.get("merged_universe")
        if not isinstance(merged_name, str):
            merged_name = f"{first.name}+{second.name}"
        merged_layers = first.layers | second.layers | set(map(str, fractal_signal.get("convergence_layers", [])))
        merged_stability = (first.stability + second.stability) / 2
        merged = ArtifactUniverse(
            name=merged_name,
            stability=merged_stability,
            layers=merged_layers,
            artifact_count=first.artifact_count + second.artifact_count,
            lineage=list(dict.fromkeys(first.lineage + second.lineage)),
        )
        self._universes[merged.name] = merged
        return merged

    def _collapse_universe(self) -> str:
        name, _ = min(self._universes.items(), key=lambda item: item[1].stability)
        self._universes.pop(name)
        return name

    def _maybe_forge_prime_artifacts(
        self,
        universe_name: str | None,
        fractal_signal: Mapping[str, Any],
        chronos_signal: Mapping[str, Any],
    ) -> list[PrimeArtifact]:
        if universe_name is None or universe_name not in self._universes:
            return []

        layers = self._collect_layers(fractal_signal, chronos_signal)
        required = {"fractal", "temporal", "narrative", "lineage"}
        if not required.issubset(layers):
            return []

        universe = self._universes[universe_name]
        artifact = self._forge_prime_artifact(universe, layers, fractal_signal, chronos_signal)
        universe.artifact_count += 1
        universe.layers.update(layers)
        self._prime_artifacts.append(artifact)
        return [artifact]

    def _collect_layers(
        self,
        fractal_signal: Mapping[str, Any],
        chronos_signal: Mapping[str, Any],
    ) -> set[str]:
        layers = set(map(str, fractal_signal.get("active_layers", [])))
        layers.update(map(str, fractal_signal.get("convergence_layers", [])))
        layers.update(map(str, fractal_signal.get("lineage_layers", [])))
        if fractal_signal.get("lineage_map"):
            layers.add("lineage")

        chronos_layers = set(map(str, chronos_signal.get("temporal_layers", [])))
        if chronos_layers:
            layers.update(chronos_layers)
        if chronos_signal.get("timeline") or chronos_signal.get("temporal_signature"):
            layers.add("temporal")

        narrative_layers = set(map(str, chronos_signal.get("narrative_layers", [])))
        if narrative_layers:
            layers.update(narrative_layers)
        if chronos_signal.get("narrative_density") or chronos_signal.get("story"):
            layers.add("narrative")

        lineage = set(map(str, chronos_signal.get("lineage_layers", [])))
        if lineage:
            layers.update(lineage)
        if fractal_signal.get("lineage_trace"):
            layers.add("lineage")

        return {layer for layer in layers if layer}

    def _forge_prime_artifact(
        self,
        universe: ArtifactUniverse,
        layers: set[str],
        fractal_signal: Mapping[str, Any],
        chronos_signal: Mapping[str, Any],
    ) -> PrimeArtifact:
        ordered_layers = tuple(sorted(layers))
        signature_source = "|".join(
            [
                universe.name,
                ",".join(ordered_layers),
                str(fractal_signal.get("narrative_seed", "")),
                str(chronos_signal.get("temporal_signature", chronos_signal.get("timeline", ""))),
                str(self._cycle),
            ]
        )
        signature = sha256(signature_source.encode("utf-8")).hexdigest()
        identifier = f"PRIME-{universe.name}-{len(self._prime_artifacts) + 1}"
        metadata: MutableMapping[str, Any] = {
            "cycle": self._cycle,
            "universe_layers": list(ordered_layers),
            "narrative": chronos_signal.get("story") or fractal_signal.get("narrative"),
            "lineage_trace": list(fractal_signal.get("lineage_trace", []))
            if isinstance(fractal_signal.get("lineage_trace"), Iterable)
            and not isinstance(fractal_signal.get("lineage_trace"), (str, bytes))
            else [],
        }
        return PrimeArtifact(
            identifier=identifier,
            universe=universe.name,
            layers=ordered_layers,
            signature=signature,
            metadata=metadata,
        )

    def _known_layers(self) -> set[str]:
        layers: set[str] = set()
        for universe in self._universes.values():
            layers.update(universe.layers)
        return layers


__all__ = [
    "SingularityCore",
    "SingularityDecision",
    "PrimeArtifact",
    "ArtifactUniverse",
    "CosmosEngine",
    "FractalEngine",
    "ChronosEngine",
]

