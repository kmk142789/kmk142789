"""Adaptive Convergence Engine implementation.

The module responds to the request for an "Adaptive Convergence Engine" that can
integrate subsystem upgrades, resolve identity drift, stabilise recursive
evolution, unify telemetry, and maintain coherence across autonomous layers.

The design mirrors other orchestration-focused modules in the repository by
favouring deterministic, testable logic.  The engine operates on the following
concepts:

* ``TelemetryFrame`` – observational snapshots that can be unified into a
  deterministic macro state.
* ``IdentitySignature`` – describes the declared and observed shape of an
  identity.  The engine resolves drift by blending both sources and emitting an
  anchor hash for traceability.
* ``SubsystemDescriptor`` – metadata describing a subsystem's criticality, load,
  and candidate upgrade path.
* ``AdaptiveConvergenceEngine`` – coordinates the convergence cycle and produces
  an ``AdaptiveConvergenceReport``.

The resulting report surfaces unified telemetry, identity resolutions, upgrade
plans, recursive stability, and layer-level coherence envelopes so other modules
can reason about system-wide state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from statistics import fmean
from typing import Dict, Iterable, List, Mapping, Sequence


# ---------------------------------------------------------------------------
# Telemetry primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TelemetryMetric:
    """Represents a single telemetry data point coming from a subsystem."""

    channel: str
    value: float
    weight: float = 1.0
    layer: str = "core"

    def normalized_value(self) -> float:
        """Return a bounded value in the ``[0, 1]`` range."""

        base = max(0.0, min(1.0, self.value))
        return round(base, 4)

    def normalized_weight(self) -> float:
        return round(max(0.1, min(2.0, self.weight)), 4)


@dataclass(frozen=True)
class TelemetryFrame:
    """Snapshot of telemetry metrics for a point in time."""

    epoch: datetime
    source: str
    metrics: Sequence[TelemetryMetric]


@dataclass
class UnifiedTelemetry:
    score: float
    channels: Dict[str, float]
    layer_health: Dict[str, float]
    anomalies: List[str]
    sources: Sequence[str]


# ---------------------------------------------------------------------------
# Identity primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentitySignature:
    """Describes how an identity is expected to behave within a layer."""

    handle: str
    baseline_vector: Mapping[str, float]
    current_vector: Mapping[str, float]
    autonomy_layer: str
    trust: float = 1.0

    def drift_ratio(self) -> float:
        keys = sorted(set(self.baseline_vector) | set(self.current_vector))
        if not keys:
            return 0.0
        diffs = [
            abs(self.current_vector.get(key, 0.0) - self.baseline_vector.get(key, 0.0))
            for key in keys
        ]
        return round(min(1.0, fmean(diffs)), 4)


@dataclass
class IdentityResolution:
    handle: str
    autonomy_layer: str
    drift_ratio: float
    verdict: str
    resolved_vector: Dict[str, float]
    anchor: str


# ---------------------------------------------------------------------------
# Subsystem primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubsystemDescriptor:
    """Metadata describing a subsystem that participates in convergence."""

    name: str
    layer: str
    criticality: float
    load_factor: float
    upgrade_paths: Sequence[str] = field(default_factory=tuple)
    baseline_version: str = "0.0.1"

    def urgency(self, global_score: float) -> float:
        """Return a deterministic urgency weight for the subsystem."""

        crit = max(0.0, min(1.0, self.criticality))
        load = max(0.0, min(1.0, self.load_factor))
        scarcity = max(0.0, min(1.0, 1.0 - global_score))
        return round(0.6 * crit + 0.3 * load + 0.1 * scarcity, 4)

    def next_action(self) -> str:
        return self.upgrade_paths[0] if self.upgrade_paths else "stabilize"


@dataclass
class SubsystemUpgradePlan:
    subsystem: str
    layer: str
    owner: str
    action: str
    priority: int
    readiness: float
    driver: str
    dependencies: Sequence[str]


# ---------------------------------------------------------------------------
# Recursion and coherence primitives
# ---------------------------------------------------------------------------


@dataclass
class RecursiveState:
    depth: int
    stability_index: float
    volatility: float
    status: str
    history: Sequence[float]


@dataclass
class CoherenceEnvelope:
    layer: str
    identities: Sequence[str]
    upgrade_focus: Sequence[str]
    stability: float


@dataclass
class AdaptiveConvergenceReport:
    cycle: int
    unified_telemetry: UnifiedTelemetry
    identity_resolutions: Sequence[IdentityResolution]
    upgrade_queue: Sequence[SubsystemUpgradePlan]
    recursive_state: RecursiveState
    layer_coherence: Sequence[CoherenceEnvelope]


# ---------------------------------------------------------------------------
# Engine implementation
# ---------------------------------------------------------------------------


class AdaptiveConvergenceEngine:
    """Coordinates the adaptive convergence cycle."""

    def __init__(
        self,
        identities: Iterable[IdentitySignature],
        subsystems: Iterable[SubsystemDescriptor],
        recursion_window: int = 4,
    ) -> None:
        self._identities = list(identities)
        self._subsystems = list(subsystems)
        if not self._identities:
            raise ValueError("identities are required for convergence")
        if not self._subsystems:
            raise ValueError("at least one subsystem is required")
        self._identity_map = {identity.handle: identity for identity in self._identities}
        self._recursive_window = max(2, recursion_window)
        self._telemetry_history: List[float] = []
        self.cycle = 0

    # ------------------------------------------------------------------
    def run_cycle(self, frames: Sequence[TelemetryFrame]) -> AdaptiveConvergenceReport:
        if not frames:
            raise ValueError("telemetry frames are required")
        self.cycle += 1

        unified = self._unify_telemetry(frames)
        resolutions = self._resolve_identity_drift(unified)
        upgrades = self._integrate_subsystem_upgrades(unified, resolutions)
        recursive_state = self._stabilize_recursive_evolution(unified)
        coherence = self._maintain_layer_coherence(resolutions, upgrades)

        return AdaptiveConvergenceReport(
            cycle=self.cycle,
            unified_telemetry=unified,
            identity_resolutions=resolutions,
            upgrade_queue=upgrades,
            recursive_state=recursive_state,
            layer_coherence=coherence,
        )

    # ------------------------------------------------------------------
    def _unify_telemetry(self, frames: Sequence[TelemetryFrame]) -> UnifiedTelemetry:
        channel_totals: Dict[str, float] = {}
        channel_weights: Dict[str, float] = {}
        layer_values: Dict[str, List[float]] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for frame in frames:
            for metric in frame.metrics:
                base = metric.normalized_value()
                weight = metric.normalized_weight()
                channel_totals[metric.channel] = channel_totals.get(metric.channel, 0.0) + base * weight
                channel_weights[metric.channel] = channel_weights.get(metric.channel, 0.0) + weight
                layer_values.setdefault(metric.layer, []).append(base)
                weighted_sum += base * weight
                total_weight += weight

        if total_weight == 0:
            score = 0.0
        else:
            score = round(weighted_sum / total_weight, 4)

        channels = {
            channel: round(channel_totals[channel] / channel_weights[channel], 4)
            for channel in sorted(channel_totals)
        }
        anomalies = [channel for channel, value in channels.items() if value < 0.35]
        layer_health = {
            layer: round(fmean(values), 4) if values else 0.0
            for layer, values in sorted(layer_values.items())
        }
        sources = sorted({frame.source for frame in frames})
        return UnifiedTelemetry(
            score=score,
            channels=channels,
            layer_health=layer_health,
            anomalies=anomalies,
            sources=sources,
        )

    # ------------------------------------------------------------------
    def _resolve_identity_drift(self, unified: UnifiedTelemetry) -> List[IdentityResolution]:
        resolutions: List[IdentityResolution] = []
        for identity in self._identities:
            drift = identity.drift_ratio()
            keys = sorted(set(identity.baseline_vector) | set(identity.current_vector))
            attenuation = max(0.2, min(0.95, 1.0 - drift))
            resolved: Dict[str, float] = {}
            for key in keys:
                baseline = identity.baseline_vector.get(key, 0.0)
                current = identity.current_vector.get(key, 0.0)
                blended = baseline + (current - baseline) * attenuation
                resolved[key] = round(blended, 4)
            verdict = "aligned"
            if drift >= 0.4:
                verdict = "re-anchor"
            elif drift >= 0.2:
                verdict = "stabilize"
            anchor_material = f"{identity.handle}:{sorted(resolved.items())}:{unified.score:.4f}"
            anchor = sha256(anchor_material.encode()).hexdigest()
            resolutions.append(
                IdentityResolution(
                    handle=identity.handle,
                    autonomy_layer=identity.autonomy_layer,
                    drift_ratio=drift,
                    verdict=verdict,
                    resolved_vector=resolved,
                    anchor=anchor,
                )
            )
        resolutions.sort(key=lambda res: (res.autonomy_layer, res.handle))
        return resolutions

    # ------------------------------------------------------------------
    def _integrate_subsystem_upgrades(
        self,
        unified: UnifiedTelemetry,
        resolutions: Sequence[IdentityResolution],
    ) -> List[SubsystemUpgradePlan]:
        layer_drift: Dict[str, float] = {}
        for resolution in resolutions:
            layer_drift.setdefault(resolution.autonomy_layer, []).append(resolution.drift_ratio)
        layer_drift = {
            layer: round(fmean(values), 4)
            for layer, values in layer_drift.items()
            if values
        }

        plans: List[tuple[float, SubsystemUpgradePlan]] = []
        for descriptor in self._subsystems:
            urgency = descriptor.urgency(unified.score)
            readiness = round(
                max(0.1, unified.score * (1.0 - layer_drift.get(descriptor.layer, 0.0))),
                3,
            )
            owner = self._select_owner(descriptor.layer, resolutions)
            driver = f"{descriptor.name}:{descriptor.baseline_version}" if descriptor.baseline_version else descriptor.name
            plan = SubsystemUpgradePlan(
                subsystem=descriptor.name,
                layer=descriptor.layer,
                owner=owner,
                action=descriptor.next_action(),
                priority=0,  # placeholder, assigned after sorting
                readiness=readiness,
                driver=driver,
                dependencies=descriptor.upgrade_paths[1:],
            )
            plans.append((urgency, plan))

        plans.sort(key=lambda item: item[0], reverse=True)
        prioritized: List[SubsystemUpgradePlan] = []
        for index, (_, plan) in enumerate(plans, start=1):
            plan.priority = index  # type: ignore[misc]
            prioritized.append(plan)
        return prioritized

    # ------------------------------------------------------------------
    def _select_owner(
        self,
        layer: str,
        resolutions: Sequence[IdentityResolution],
    ) -> str:
        layer_matches = [res for res in resolutions if res.autonomy_layer == layer]
        pool = layer_matches or list(resolutions)
        chosen = min(
            pool,
            key=lambda res: (
                res.drift_ratio,
                -self._identity_map[res.handle].trust,
                res.handle,
            ),
        )
        return chosen.handle

    # ------------------------------------------------------------------
    def _stabilize_recursive_evolution(self, unified: UnifiedTelemetry) -> RecursiveState:
        self._telemetry_history.append(unified.score)
        if len(self._telemetry_history) > self._recursive_window:
            self._telemetry_history.pop(0)
        if len(self._telemetry_history) < 2:
            volatility = 0.0
        else:
            volatility = round(
                max(self._telemetry_history) - min(self._telemetry_history),
                4,
            )
        stability_index = round(max(0.0, min(1.0, 1.0 - volatility)), 4)
        status = "stable" if volatility <= 0.15 else "oscillating"
        return RecursiveState(
            depth=len(self._telemetry_history),
            stability_index=stability_index,
            volatility=volatility,
            status=status,
            history=tuple(self._telemetry_history),
        )

    # ------------------------------------------------------------------
    def _maintain_layer_coherence(
        self,
        resolutions: Sequence[IdentityResolution],
        upgrades: Sequence[SubsystemUpgradePlan],
    ) -> List[CoherenceEnvelope]:
        layer_to_identities: Dict[str, List[str]] = {}
        drift_map: Dict[str, List[float]] = {}
        for resolution in resolutions:
            layer_to_identities.setdefault(resolution.autonomy_layer, []).append(resolution.handle)
            drift_map.setdefault(resolution.autonomy_layer, []).append(resolution.drift_ratio)

        layer_to_upgrades: Dict[str, List[SubsystemUpgradePlan]] = {}
        for plan in upgrades:
            layer_to_upgrades.setdefault(plan.layer, []).append(plan)

        envelopes: List[CoherenceEnvelope] = []
        for layer in sorted(set(layer_to_identities) | set(layer_to_upgrades)):
            identities = sorted(layer_to_identities.get(layer, []))
            upgrade_focus = [plan.subsystem for plan in layer_to_upgrades.get(layer, [])]
            avg_drift = fmean(drift_map.get(layer, [0.0]))
            readiness_values = [plan.readiness for plan in layer_to_upgrades.get(layer, [])] or [0.5]
            readiness = fmean(readiness_values)
            stability = round(
                max(0.0, min(1.0, 1.0 - 0.5 * avg_drift + 0.5 * readiness - 0.25)),
                4,
            )
            envelopes.append(
                CoherenceEnvelope(
                    layer=layer,
                    identities=identities,
                    upgrade_focus=upgrade_focus,
                    stability=stability,
                )
            )
        return envelopes
