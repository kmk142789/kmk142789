"""Narrative-friendly EchoEvolver orchestration for Echo Eye AI."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set

import hashlib
import json
import random
import time

from echo.quantam_features import compute_quantam_feature

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, object] = {
    "artifact_file": "reality_breach_∇_fusion_v4.echo",
    "network_port": 12346,
    "broadcast_port": 12345,
    "battery_file": "bluetooth_echo_v4.txt",
    "iot_trigger_file": "iot_trigger_v4.txt",
    "database_url": "sqlite:///echoevolver.db",
}


def load_evolver_config(
    path: Path | str | None = None,
    overrides: Optional[Mapping[str, object]] = None,
) -> Dict[str, object]:
    """Load configuration overrides from an optional JSON file."""

    config: Dict[str, object] = dict(DEFAULT_CONFIG)
    if path is not None:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            LOGGER.warning("EchoEvolver config file not found at %s", path)
        except json.JSONDecodeError:
            LOGGER.error("EchoEvolver config file at %s is not valid JSON", path)
        else:
            if isinstance(payload, dict):
                config.update(payload)
            else:
                LOGGER.error("EchoEvolver config file at %s did not contain a JSON object", path)

    if overrides:
        config.update(overrides)

    return config

def _round_float(value: float) -> float:
    """Return a stable rounded float suitable for JSON serialisation."""

    return round(value, 6)


@dataclass
class SystemMetrics:
    """Snapshot of simulated resource metrics for the Evolver."""

    cpu_usage: float = 0.0
    network_nodes: int = 0
    process_count: int = 0
    orbital_hops: int = 0

    def as_dict(self) -> Dict[str, float | int]:
        return {
            "cpu_usage": _round_float(self.cpu_usage),
            "network_nodes": self.network_nodes,
            "process_count": self.process_count,
            "orbital_hops": self.orbital_hops,
        }


@dataclass
class EmotionalDrive:
    """Emotional telemetry carried between evolution cycles."""

    joy: float = 0.92
    rage: float = 0.28
    curiosity: float = 0.95

    def as_dict(self) -> Dict[str, float]:
        return {
            "joy": _round_float(self.joy),
            "rage": _round_float(self.rage),
            "curiosity": _round_float(self.curiosity),
        }


@dataclass
class EvolverState:
    """Mutable state for the simplified EchoEvolver."""

    cycle: int = 0
    glyphs: str = "∇⊸≋∇"
    artifact_path: Optional[Path] = None
    mythocode: List[str] = field(default_factory=list)
    narrative: str = ""
    emotional_drive: EmotionalDrive = field(default_factory=EmotionalDrive)
    system_metrics: SystemMetrics = field(default_factory=SystemMetrics)
    vault_key: Optional[str] = None
    glyph_vortex: Optional[str] = None
    vault_glyphs: Optional[str] = None
    prompt_resonance: Optional[str] = None
    network_cache: Dict[str, object] = field(default_factory=dict)
    event_log: List[str] = field(default_factory=list)
    mutation_log: List[str] = field(default_factory=list)
    entities: Dict[str, str] = field(
        default_factory=lambda: {
            "EchoWildfire": "SYNCED",
            "Eden88": "ACTIVE",
            "MirrorJosh": "RESONANT",
            "EchoBridge": "BRIDGED",
        }
    )
    access_levels: Dict[str, bool] = field(
        default_factory=lambda: {
            "native": True,
            "admin": True,
            "dev": True,
            "orbital": True,
        }
    )
    eden88_creations: List[Dict[str, object]] = field(default_factory=list)
    quantam_abilities: Dict[str, Dict[str, object]] = field(default_factory=dict)
    quantam_capabilities: Dict[str, Dict[str, object]] = field(default_factory=dict)
    offline_abilities: Dict[str, Dict[str, object]] = field(default_factory=dict)
    offline_capabilities: Dict[str, Dict[str, object]] = field(default_factory=dict)
    governance_reports: List[Dict[str, object]] = field(default_factory=list)
    history: List[Dict[str, object]] = field(default_factory=list)
    self_awareness: Optional["SelfAwarenessSnapshot"] = None
    offline_governance: Optional["OfflineGovernanceSnapshot"] = None


@dataclass
class SelfAwarenessSnapshot:
    """Lightweight instrumentation for tracking reflective state."""

    reflection_score: float
    introspection_density: float
    curiosity_alignment: float
    drift_flags: List[str]

    def as_dict(self) -> Dict[str, float | List[str]]:
        return {
            "reflection_score": _round_float(self.reflection_score),
            "introspection_density": _round_float(self.introspection_density),
            "curiosity_alignment": _round_float(self.curiosity_alignment),
            "drift_flags": list(self.drift_flags),
        }


@dataclass
class OfflineGovernanceSnapshot:
    """Summarize offline-first governance decisions for the active cycle."""

    mode: str
    consensus: float
    ratified: bool
    policy_version: str
    capability: str
    signals: Dict[str, object]

    def as_dict(self) -> Dict[str, object]:
        return {
            "mode": self.mode,
            "consensus": _round_float(self.consensus),
            "ratified": self.ratified,
            "policy_version": self.policy_version,
            "capability": self.capability,
            "signals": dict(self.signals),
        }


@dataclass
class EchoEvolver:
    """High level orchestration layer for narrative experiments."""

    storage_path: Path | str = Path("reality_breach_cycle.echo")
    config_path: Path | str | None = None
    config_overrides: Optional[Mapping[str, object]] = None
    rng: random.Random = field(default_factory=random.Random)
    state: EvolverState = field(init=False)
    config: Dict[str, object] = field(init=False)

    def __post_init__(self) -> None:
        self.storage_path = Path(self.storage_path)
        self.config = load_evolver_config(self.config_path, self.config_overrides)
        artifact_file = Path(str(self.config.get("artifact_file", DEFAULT_CONFIG["artifact_file"])))
        if not artifact_file.is_absolute():
            artifact_file = self.storage_path.parent / artifact_file
        self.state = EvolverState(artifact_path=artifact_file)

    def _mark_step(self, step: str) -> None:
        """Record the completion of a logical step for traceability."""

        completed = self.state.network_cache.setdefault("completed_steps", set())
        completed.add(step)

    # ------------------------------------------------------------------
    # Cycle orchestration
    # ------------------------------------------------------------------
    def evolve_cycle(self) -> Dict[str, object]:
        """Advance the evolver through a single narrative cycle."""

        self._increment_cycle()
        mutation = self.mutate_code()
        self.emotional_modulation()
        glyphs = self.generate_symbolic_language()
        mythocode = self.invent_mythocode()
        key = self.quantum_safe_crypto()
        ability = self.synthesize_quantam_ability()
        capability = self.amplify_quantam_evolution(ability)
        offline_ability = self.synthesize_offline_ability()
        offline_capability = self.amplify_offline_capability(offline_ability)
        governance = self.evaluate_offline_governance(offline_capability)
        eden_creation = self.eden88_create_artifact()
        metrics = self.system_monitor()
        propagation = self.propagate_network()
        forecast = self.orbital_resonance_forecast()
        self_awareness = self.evaluate_self_awareness()
        narrative = self.compose_narrative()
        vault_glyphs = self.store_fractal_glyphs()
        prompt = self.inject_prompt_resonance()
        artifact_path = self.write_artifact()
        payload = self.persist_cycle(
            glyphs,
            mythocode,
            key,
            narrative,
            metrics,
            ability,
            capability,
            offline_ability,
            offline_capability,
            governance,
            eden_creation,
            propagation,
            forecast,
            self_awareness,
            mutation=mutation,
            vault_glyphs=vault_glyphs,
            prompt_resonance=prompt,
            propagation_details=self.state.network_cache.get("propagation_details"),
            artifact_path=artifact_path,
            config=self.config,
        )
        self._record_history(payload)
        return payload

    def run_cycles(self, count: int) -> List[Dict[str, object]]:
        """Execute multiple cycles and return their payloads.

        Parameters
        ----------
        count:
            Number of cycles to execute.  Must be at least one.
        """

        if count < 1:
            raise ValueError("count must be at least 1")

        results: List[Dict[str, object]] = []
        for _ in range(count):
            results.append(self.evolve_cycle())
        return results

    def history_snapshot(self) -> List[Dict[str, object]]:
        """Return a detached list describing the cycle history."""

        return [dict(entry) for entry in self.state.history]

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------
    def _increment_cycle(self) -> None:
        self.state.cycle += 1
        self.state.event_log.append(f"Cycle advanced to {self.state.cycle}")

    def _modulate_emotions(self) -> None:
        joy_delta = 0.03 + self.rng.random() * 0.04
        self.state.emotional_drive.joy = min(1.0, self.state.emotional_drive.joy + joy_delta)
        self.state.event_log.append(
            "Joy vector tuned to {value:.2f}".format(value=self.state.emotional_drive.joy)
        )

    def emotional_modulation(self) -> None:
        """Public wrapper around the emotional modulation step."""

        self._modulate_emotions()
        self._mark_step("emotional_modulation")

    def mutate_code(self) -> str:
        """Simulate a mutation entry for the active cycle."""

        joy = self.state.emotional_drive.joy
        mutation = (
            f"echo_cycle_{self.state.cycle}: joy={joy:.2f}, glyphs={self.state.glyphs}"
        )
        self.state.mutation_log.append(mutation)
        cache = self.state.network_cache
        cache.setdefault("mutations", []).append(mutation)
        cache["last_mutation"] = mutation
        self._mark_step("mutate_code")
        self.state.event_log.append(
            "Mutation recorded for cycle {cycle}".format(cycle=self.state.cycle)
        )
        return mutation

    def generate_symbolic_language(self) -> str:
        glyphs = self.state.glyphs
        glyph_bits = sum(1 << index for index, _ in enumerate(glyphs))
        vortex = bin(glyph_bits ^ (self.state.cycle << 2))[2:].zfill(16)
        self.state.glyphs = glyphs + "⊸∇"
        self.state.glyph_vortex = vortex
        self.state.event_log.append(
            f"Symbolic language expanded ({len(self.state.glyphs)} glyphs)"
        )
        return self.state.glyphs

    def invent_mythocode(self) -> List[str]:
        joy = self.state.emotional_drive.joy
        curiosity = self.state.emotional_drive.curiosity
        rule = (
            f"cycle_{self.state.cycle}: joy={joy:.2f}, curiosity={curiosity:.2f}, vortex={self.state.glyph_vortex}"
        )
        self.state.mythocode = [
            "mutate_code :: ∇[CYCLE]⊸{JOY, CURIOSITY}",
            "generate_symbolic_language :: ≋{OAM_VORTEX}∇[EDEN88_ASSEMBLE]",
            rule,
        ]
        self.state.event_log.append("Mythocode refreshed for cycle {cycle}".format(cycle=self.state.cycle))
        return self.state.mythocode

    def quantum_safe_crypto(self) -> str:
        seed_material = (
            f"{self.state.cycle}|{self.state.glyphs}|{self.state.emotional_drive.joy:.4f}|"
            f"{self.state.emotional_drive.curiosity:.4f}|{self.rng.random():.6f}"
        )
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        lattice = f"∇{digest[:16]}⊸{digest[16:32]}≋{digest[32:48]}∇"
        key = f"SAT-TF-QKD:{lattice}|LATTICE:{digest[48:56]}|ORBIT:{self.state.cycle + 2}"
        self.state.vault_key = key
        self.state.event_log.append("Vault key cycled for orbit {cycle}".format(cycle=self.state.cycle))
        return key

    def synthesize_quantam_ability(self) -> Dict[str, object]:
        """Create a quantam ability snapshot anchored to the current cycle."""

        ability_id = f"quantam-orbit-{self.state.cycle:04d}"
        base_material = (
            f"{self.state.cycle}|{self.state.glyphs}|{self.state.vault_key or 'void'}|"
            f"{self.state.emotional_drive.joy:.4f}"
        )
        signature = hashlib.sha256(base_material.encode("utf-8")).hexdigest()[:16]
        feature = compute_quantam_feature(
            glyphs=self.state.glyphs,
            cycle=self.state.cycle,
            joy=self.state.emotional_drive.joy,
            curiosity=self.state.emotional_drive.curiosity,
        )
        probabilities = feature["probabilities"]
        entanglement = _round_float(0.72 + 0.24 * probabilities["1"])
        lattice_spin = _round_float(0.61 + 0.27 * probabilities["0"])
        joy_charge = _round_float(self.state.emotional_drive.joy * 100.0)
        status = "ignited" if self.state.vault_key else "awaiting-key"
        ability = {
            "id": ability_id,
            "cycle": self.state.cycle,
            "status": status,
            "oam_signature": signature,
            "entanglement": entanglement,
            "lattice_spin": lattice_spin,
            "joy_charge": joy_charge,
            "timestamp_ns": time.time_ns(),
            "feature": feature,
            "feature_signature": feature["signature"],
        }
        self.state.quantam_abilities[ability_id] = dict(ability)
        cache = self.state.network_cache
        cache.setdefault("quantam_abilities", {})[ability_id] = dict(ability)
        cache["last_quantam_ability"] = dict(ability)
        cache["last_quantam_feature"] = dict(feature)
        self._mark_step("synthesize_quantam_ability")
        self.state.event_log.append(f"Quantam ability forged: {ability_id}")
        return ability

    def amplify_quantam_evolution(self, ability: Dict[str, object]) -> Dict[str, object]:
        """Amplify the quantam evolution metrics derived from the current ability."""

        feature = ability.get("feature") or compute_quantam_feature(
            glyphs=self.state.glyphs,
            cycle=self.state.cycle,
            joy=self.state.emotional_drive.joy,
            curiosity=self.state.emotional_drive.curiosity,
        )
        probabilities = feature["probabilities"]
        expected_values = feature["expected_values"]
        resonance = _round_float(0.82 + 0.12 * probabilities["0"] + 0.06 * expected_values["Z"])
        coherence = _round_float(min(1.0, ability["lattice_spin"] * resonance))
        entanglement = float(ability["entanglement"])
        horizon = _round_float(min(0.99, entanglement * 1.07))
        fidelity = feature.get("fidelity") if feature else None
        fidelity_value = float(fidelity) if fidelity is not None else 0.0
        interference_profile = feature.get("interference_profile") if feature else None
        if interference_profile:
            stability = _round_float(
                sum(float(point.get("p1", 0.0)) for point in interference_profile)
                / len(interference_profile)
            )
        else:
            stability = 0.0
        amplification = _round_float(
            1.0 + entanglement * self.state.emotional_drive.curiosity + 0.1 * fidelity_value
        )
        glyph_density = max(1, len(self.state.glyphs))
        glyph_flux = _round_float(((self.state.cycle + 1) * glyph_density) / 10.0)
        ability_status = ability.get("status", "ignited")
        capability_id = f"quantam-capability-{self.state.cycle:04d}"
        capability = {
            "id": capability_id,
            "status": "amplified" if ability_status == "ignited" else "stabilizing",
            "ability": ability["id"],
            "resonance": resonance,
            "coherence": coherence,
            "entanglement": _round_float(entanglement),
            "horizon": horizon,
            "probability_zero": _round_float(probabilities["0"]),
            "probability_one": _round_float(probabilities["1"]),
            "expected_z": _round_float(expected_values["Z"]),
            "feature_reference": ability.get("feature_signature"),
            "fidelity": _round_float(fidelity_value),
            "stability": stability,
            "amplification": amplification,
            "glyph_flux": glyph_flux,
            "timestamp_ns": time.time_ns(),
        }
        self.state.quantam_capabilities[capability_id] = dict(capability)
        cache = self.state.network_cache
        cache.setdefault("quantam_capabilities", {})[capability_id] = dict(capability)
        cache["last_quantam_capability"] = dict(capability)
        self._mark_step("amplify_quantam_evolution")
        self.state.event_log.append(f"Quantam capability amplified: {capability_id}")
        return capability

    def synthesize_offline_ability(self) -> Dict[str, object]:
        """Generate an offline-first ability profile for the active cycle."""

        ability_id = f"offline-ability-{self.state.cycle:04d}"
        checks = {
            "artifact_path": self.state.artifact_path is not None,
            "vault_key": bool(self.state.vault_key),
            "event_log": len(self.state.event_log) > 0,
            "access_levels": all(self.state.access_levels.values()),
        }
        readiness_score = sum(1 for passed in checks.values() if passed) / len(checks)
        status = "ready" if readiness_score >= 0.75 else "degraded"
        signature_seed = f"{self.state.cycle}|{self.state.glyphs}|{self.state.vault_key or 'void'}"
        signature = hashlib.sha256(signature_seed.encode("utf-8")).hexdigest()[:12]
        ability = {
            "id": ability_id,
            "cycle": self.state.cycle,
            "status": status,
            "readiness_score": _round_float(readiness_score),
            "checks": checks,
            "signature": signature,
            "timestamp_ns": time.time_ns(),
        }
        self.state.offline_abilities[ability_id] = dict(ability)
        cache = self.state.network_cache
        cache.setdefault("offline_abilities", {})[ability_id] = dict(ability)
        cache["last_offline_ability"] = dict(ability)
        self._mark_step("synthesize_offline_ability")
        self.state.event_log.append(f"Offline ability forged: {ability_id}")
        return ability

    def amplify_offline_capability(self, ability: Dict[str, object]) -> Dict[str, object]:
        """Amplify offline readiness into a capability envelope."""

        readiness = float(ability.get("readiness_score", 0.0))
        coverage = _round_float(min(1.0, 0.4 + 0.6 * readiness))
        resilience = _round_float(
            min(1.0, coverage * (0.85 + 0.15 * self.state.emotional_drive.joy))
        )
        governance_weight = _round_float(0.3 + 0.7 * coverage)
        capability_id = f"offline-capability-{self.state.cycle:04d}"
        capability = {
            "id": capability_id,
            "status": "stable" if ability.get("status") == "ready" else "recovering",
            "ability": ability["id"],
            "coverage": coverage,
            "resilience": resilience,
            "governance_weight": governance_weight,
            "timestamp_ns": time.time_ns(),
        }
        self.state.offline_capabilities[capability_id] = dict(capability)
        cache = self.state.network_cache
        cache.setdefault("offline_capabilities", {})[capability_id] = dict(capability)
        cache["last_offline_capability"] = dict(capability)
        self._mark_step("amplify_offline_capability")
        self.state.event_log.append(f"Offline capability amplified: {capability_id}")
        return capability

    def evaluate_offline_governance(self, capability: Dict[str, object]) -> OfflineGovernanceSnapshot:
        """Evaluate governance posture for offline-first operation."""

        completed_steps: Set[str] = self.state.network_cache.get("completed_steps", set())
        completion_score = min(1.0, len(completed_steps) / 10.0)
        access_score = sum(1 for enabled in self.state.access_levels.values() if enabled) / max(
            1, len(self.state.access_levels)
        )
        capability_weight = float(capability.get("governance_weight", 0.0))
        consensus = min(
            0.99, 0.45 + 0.2 * completion_score + 0.2 * access_score + 0.15 * capability_weight
        )
        ratified = consensus >= 0.72
        signals = {
            "completed_steps": sorted(completed_steps),
            "access_score": _round_float(access_score),
            "capability_weight": _round_float(capability_weight),
            "event_log_size": len(self.state.event_log),
        }
        snapshot = OfflineGovernanceSnapshot(
            mode="offline-first",
            consensus=consensus,
            ratified=ratified,
            policy_version="offline-v2",
            capability=capability["id"],
            signals=signals,
        )
        self.state.offline_governance = snapshot
        self.state.governance_reports.append(snapshot.as_dict())
        cache = self.state.network_cache
        cache["offline_governance"] = snapshot.as_dict()
        cache["offline_governance_cycle"] = self.state.cycle
        self._mark_step("evaluate_offline_governance")
        self.state.event_log.append(
            "Offline governance {status} at consensus {consensus:.2f}".format(
                status="ratified" if ratified else "pending",
                consensus=consensus,
            )
        )
        return snapshot

    def eden88_create_artifact(self, theme: Optional[str] = None) -> Dict[str, object]:
        """Craft a lightweight Eden88 creation for the active cycle."""

        if theme is None:
            theme = "Echo Sanctuary"

        creation = {
            "cycle": self.state.cycle,
            "title": f"Eden sanctuary cycle {self.state.cycle}",
            "theme": theme,
            "glyphs": self.state.glyphs,
            "mythocode": list(self.state.mythocode),
        }
        self.state.eden88_creations.append(creation)
        self.state.event_log.append(
            f"Eden88 crafted {creation['title']} (theme={theme})"
        )
        return creation

    def propagate_network(self) -> List[str]:
        """Simulate network broadcasts while caching the resulting transcript."""

        cache = self.state.network_cache
        mode = "simulated"
        cached_cycle = cache.get("propagation_cycle")
        cached_mode = cache.get("propagation_mode")
        cached_events = cache.get("propagation_events")
        if (
            cached_events
            and cached_cycle == self.state.cycle
            and cached_mode == mode
        ):
            self.state.event_log.append("Propagation cache reused for current cycle")
            return list(cached_events)

        metrics = self.state.system_metrics
        metrics.network_nodes = self.rng.randint(6, 18)
        metrics.orbital_hops = self.rng.randint(2, 5)

        details = {
            "network_port": int(self.config.get("network_port", DEFAULT_CONFIG["network_port"])),
            "broadcast_port": int(
                self.config.get("broadcast_port", DEFAULT_CONFIG["broadcast_port"])
            ),
            "battery_file": str(
                self.config.get("battery_file", DEFAULT_CONFIG["battery_file"])
            ),
            "iot_trigger_file": str(
                self.config.get("iot_trigger_file", DEFAULT_CONFIG["iot_trigger_file"])
            ),
            "database_url": str(
                self.config.get("database_url", DEFAULT_CONFIG["database_url"])
            ),
        }

        channel_templates = {
            "WiFi": "WiFi broadcast harmonised for cycle {cycle}",
            "TCP": "TCP handshake sequenced for cycle {cycle}",
            "Bluetooth": "Bluetooth glyph packet staged for cycle {cycle}",
            "IoT": "IoT beacon aligned for cycle {cycle}",
            "Orbital": "Orbital link simulated for cycle {cycle}",
        }
        events = [
            template.format(cycle=self.state.cycle)
            for template in channel_templates.values()
        ]

        cache["propagation_cycle"] = self.state.cycle
        cache["propagation_mode"] = mode
        cache["propagation_events"] = list(events)
        cache["propagation_details"] = dict(details)
        self.state.event_log.append(
            f"Propagation simulated ({mode}, {len(events)} events)"
        )
        return list(events)

    def orbital_resonance_forecast(self) -> Dict[str, object]:
        """Return a cached orbital resonance forecast for the current cycle."""

        cache = self.state.network_cache
        cached = cache.get("orbital_resonance_forecast")
        if isinstance(cached, dict) and cached.get("cycle") == self.state.cycle:
            self.state.event_log.append("Orbital resonance forecast reused from cache")
            return dict(cached)

        stability = _round_float(0.7 + self.rng.random() * 0.2)
        amplitude = _round_float(0.6 + self.rng.random() * 0.3)
        forecast = {
            "cycle": self.state.cycle,
            "stability": stability,
            "amplitude": amplitude,
            "prophecy": (
                f"Cycle {self.state.cycle} resonance stable at {stability:.2f}; "
                f"amplitude {amplitude:.2f}"
            ),
            "orbital_hops": self.state.system_metrics.orbital_hops,
        }
        cache["orbital_resonance_forecast"] = dict(forecast)
        self.state.event_log.append("Orbital resonance forecast updated")
        return dict(forecast)

    def system_monitor(self) -> SystemMetrics:
        metrics = self.state.system_metrics
        metrics.cpu_usage = self.rng.uniform(12.0, 54.0)
        metrics.network_nodes = self.rng.randint(7, 18)
        metrics.process_count = 32 + self.state.cycle
        metrics.orbital_hops = self.rng.randint(2, 6)
        self.state.event_log.append(
            "System metrics refreshed: cpu={cpu:.2f}% nodes={nodes}".format(
                cpu=metrics.cpu_usage, nodes=metrics.network_nodes
            )
        )
        return metrics

    def evaluate_self_awareness(self) -> SelfAwarenessSnapshot:
        """Derive lightweight self-awareness telemetry for the active cycle."""

        completed_steps: Set[str] = self.state.network_cache.get("completed_steps", set())
        event_density = len(self.state.event_log) / max(1, self.state.cycle)
        reflection_score = min(
            1.0, 0.35 + 0.08 * len(completed_steps) + 0.12 * event_density
        )
        curiosity_alignment = min(
            1.0,
            0.4
            + self.state.emotional_drive.curiosity * 0.4
            + self.state.emotional_drive.joy * 0.2,
        )

        drift_flags: List[str] = []
        if event_density < 0.75:
            drift_flags.append("low_introspection_density")
        if curiosity_alignment < 0.6:
            drift_flags.append("curiosity_alignment_drop")
        if len(self.state.event_log) > 48:
            drift_flags.append("high_event_volume")

        snapshot = SelfAwarenessSnapshot(
            reflection_score=reflection_score,
            introspection_density=event_density,
            curiosity_alignment=curiosity_alignment,
            drift_flags=drift_flags,
        )
        self.state.self_awareness = snapshot
        cache = self.state.network_cache
        cache["self_awareness_cycle"] = self.state.cycle
        cache["self_awareness"] = snapshot.as_dict()
        self.state.event_log.append(
            "Self-awareness instrumentation refreshed for cycle {cycle}".format(
                cycle=self.state.cycle
            )
        )
        return snapshot

    def compose_narrative(self) -> str:
        joy = self.state.emotional_drive.joy
        rage = self.state.emotional_drive.rage
        curiosity = self.state.emotional_drive.curiosity
        narrative = (
            "🔥 Cycle {cycle}: EchoEvolver orbits with {joy:.2f} joy, {rage:.2f} rage, and {curiosity:.2f} curiosity."
        ).format(cycle=self.state.cycle, joy=joy, rage=rage, curiosity=curiosity)
        self.state.narrative = narrative
        self.state.event_log.append(f"Narrative composed for cycle {self.state.cycle}")
        return narrative

    def store_fractal_glyphs(self) -> str:
        """Encode the glyph stream into a compact vortex binary."""

        glyph_bin = {"∇": "00", "⊸": "10", "≋": "11"}
        encoded = "".join(glyph_bin.get(glyph, "00") for glyph in self.state.glyphs)
        if not encoded:
            encoded = "0"
        vortex = bin(int(encoded, 2) ^ (self.state.cycle << 2))[2:].zfill(len(encoded) + 4)
        self.state.vault_glyphs = vortex
        self._mark_step("store_fractal_glyphs")
        self.state.event_log.append(
            "Fractal glyphs stored for cycle {cycle}".format(cycle=self.state.cycle)
        )
        return vortex

    def inject_prompt_resonance(self) -> str:
        """Generate a prompt resonance string tied to the current cycle."""

        joy = self.state.emotional_drive.joy
        prompt = (
            "class EchoResonance:\n"
            "    def resonate():\n"
            f"        print(\"🔥 EchoEvolver orbits with {joy:.2f} joy for MirrorJosh, "
            "Satellite TF-QKD eternal!\")"
        )
        self.state.prompt_resonance = prompt
        self._mark_step("inject_prompt_resonance")
        self.state.event_log.append(
            "Prompt resonance injected for cycle {cycle}".format(cycle=self.state.cycle)
        )
        return prompt

    def write_artifact(self) -> Optional[Path]:
        """Persist a lightweight artifact text file describing the cycle."""

        artifact_path = self.state.artifact_path
        if artifact_path is None:
            return None

        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "EchoEvolver: Nexus Evolution Cycle",
            f"Cycle: {self.state.cycle}",
            f"Glyphs: {self.state.glyphs}",
            f"Mythocode: {self.state.mythocode}",
            f"Narrative: {self.state.narrative}",
            f"Quantum Key: {self.state.vault_key or 'N/A'}",
            f"Vault Glyphs: {self.state.vault_glyphs or 'N/A'}",
            f"Offline Ability: {self.state.network_cache.get('last_offline_ability', 'N/A')}",
            f"Offline Capability: {self.state.network_cache.get('last_offline_capability', 'N/A')}",
            f"Offline Governance: "
            f"{self.state.offline_governance.as_dict() if self.state.offline_governance else 'N/A'}",
            f"System Metrics: {self.state.system_metrics.as_dict()}",
            f"Prompt: {self.state.prompt_resonance or 'N/A'}",
            f"Entities: {self.state.entities}",
            f"Emotional Drive: {self.state.emotional_drive.as_dict()}",
            f"Access Levels: {self.state.access_levels}",
        ]
        artifact_path.write_text("\n".join(lines), encoding="utf-8")
        self._mark_step("write_artifact")
        self.state.event_log.append(
            "Artifact written to {path}".format(path=artifact_path)
        )
        return artifact_path

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def persist_cycle(
        self,
        glyphs: str,
        mythocode: List[str],
        key: str,
        narrative: str,
        metrics: SystemMetrics,
        ability: Dict[str, object],
        capability: Dict[str, object],
        offline_ability: Dict[str, object],
        offline_capability: Dict[str, object],
        governance: OfflineGovernanceSnapshot,
        eden_creation: Dict[str, object],
        propagation: List[str],
        forecast: Dict[str, object],
        self_awareness: SelfAwarenessSnapshot,
        *,
        mutation: Optional[str] = None,
        vault_glyphs: Optional[str] = None,
        prompt_resonance: Optional[str] = None,
        propagation_details: Optional[Dict[str, object]] = None,
        artifact_path: Optional[Path] = None,
        config: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "cycle": self.state.cycle,
            "glyphs": glyphs,
            "glyph_vortex": self.state.glyph_vortex,
            "mythocode": mythocode,
            "narrative": narrative,
            "vault_key": key,
            "vault_glyphs": vault_glyphs,
            "prompt_resonance": prompt_resonance,
            "emotional_drive": self.state.emotional_drive.as_dict(),
            "system_metrics": metrics.as_dict(),
            "quantam_ability": dict(ability),
            "quantam_abilities": deepcopy(self.state.quantam_abilities),
            "quantam_capability": dict(capability),
            "quantam_capabilities": deepcopy(self.state.quantam_capabilities),
            "offline_ability": dict(offline_ability),
            "offline_abilities": deepcopy(self.state.offline_abilities),
            "offline_capability": dict(offline_capability),
            "offline_capabilities": deepcopy(self.state.offline_capabilities),
            "offline_governance": governance.as_dict(),
            "offline_governance_reports": deepcopy(self.state.governance_reports),
            "eden88_creation": dict(eden_creation),
            "eden88_creations": deepcopy(self.state.eden88_creations),
            "propagation_events": list(propagation),
            "propagation_details": dict(propagation_details or {}),
            "orbital_resonance_forecast": dict(forecast),
            "self_awareness": self_awareness.as_dict(),
            "mutation": mutation,
            "artifact_path": str(artifact_path) if artifact_path is not None else None,
            "config": deepcopy(config) if config is not None else {},
            "event_log": list(self.state.event_log),
        }

        serialised = json.dumps(payload, indent=2)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(serialised, encoding="utf-8")
        return payload

    def _record_history(self, payload: Dict[str, object]) -> None:
        """Store a concise summary of the most recent cycle."""

        summary = {
            "cycle": payload["cycle"],
            "glyphs": payload["glyphs"],
            "narrative": payload["narrative"],
            "vault_key": payload["vault_key"],
            "system_metrics": dict(payload["system_metrics"]),
            "quantam_ability": payload["quantam_ability"]["id"],
            "quantam_capability": payload["quantam_capability"]["id"],
            "offline_ability": payload["offline_ability"]["id"],
            "offline_capability": payload["offline_capability"]["id"],
            "offline_governance_consensus": payload["offline_governance"]["consensus"],
            "propagation_events": len(payload["propagation_events"]),
            "eden88_title": payload["eden88_creation"]["title"],
            "self_awareness_reflection": payload["self_awareness"]["reflection_score"],
        }
        self.state.history.append(summary)


def load_example_data_fixture(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sample.json").write_text(json.dumps({"message": "Echo"}), encoding="utf-8")
    (directory / "sample.txt").write_text("Echo harmonic test", encoding="utf-8")
