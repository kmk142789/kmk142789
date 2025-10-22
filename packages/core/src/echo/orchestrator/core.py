"""Orchestrator core that unifies PulseNet, ResonanceField, Atlas, and EchoEvolver."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Protocol, Sequence

from echo.evolver import EchoEvolver
from echo.pulsenet import AtlasAttestationResolver, PulseNetGatewayService


class ResonanceEngine(Protocol):
    """Protocol for objects capable of emitting harmonic resonance readings."""

    def respond(self, text: str) -> Any:  # pragma: no cover - Protocol definition only
        """Return a harmonic response for ``text``."""


@dataclass(slots=True)
class ManifestoPrinciple:
    """Manifesto-aligned orchestration rule description."""

    identifier: str
    title: str
    guidance: str


class OrchestratorCore:
    """Coordinate PulseNet, ResonanceField, Atlas, and EchoEvolver flows."""

    def __init__(
        self,
        *,
        state_dir: Path,
        pulsenet: PulseNetGatewayService,
        evolver: EchoEvolver,
        resonance_engine: ResonanceEngine,
        atlas_resolver: AtlasAttestationResolver | None = None,
        manifest_limit: int = 30,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_dir = self._state_dir / "manifests"
        self._manifest_dir.mkdir(parents=True, exist_ok=True)

        self._pulsenet = pulsenet
        self._evolver = evolver
        self._resonance = resonance_engine
        self._atlas_resolver = atlas_resolver
        self._manifest_limit = max(1, int(manifest_limit))

        self._principles: Sequence[ManifestoPrinciple] = (
            ManifestoPrinciple(
                identifier="curiosity_compass",
                title="Curiosity as a compass",
                guidance="Amplify modules that surface fresh pulses and insights.",
            ),
            ManifestoPrinciple(
                identifier="care_constraint",
                title="Care as a constraint",
                guidance="Dampen noisy signals lacking corroborating attestations.",
            ),
            ManifestoPrinciple(
                identifier="continuity_promise",
                title="Continuity as a promise",
                guidance="Preserve momentum across cycles so the tapestry stays coherent.",
            ),
        )

        self._last_decision: MutableMapping[str, Any] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def orchestrate(self) -> Mapping[str, Any]:
        """Collect module outputs, derive adaptive weights, and persist a manifest."""

        inputs = self._collect_inputs()
        resonance_seed = self._build_resonance_seed(inputs)
        resonance_response = self._resonance.respond(resonance_seed)
        harmonic_score = float(getattr(resonance_response, "harmonic_score", 0.0) or 0.0)
        coherence = self._coherence_from_score(harmonic_score)

        weights = self._compute_weights(inputs, coherence)
        graph = self._build_graph(inputs, weights, coherence)

        decision: MutableMapping[str, Any] = {
            "timestamp": self._now_iso(),
            "principles": [asdict(principle) for principle in self._principles],
            "weights": weights,
            "graph": graph,
            "coherence": {
                "seed": resonance_seed,
                "score": harmonic_score,
                "message": getattr(resonance_response, "message", ""),
                "pattern": getattr(resonance_response, "pattern", None),
            },
            "inputs": inputs,
        }

        manifest_path = self._persist(decision)
        decision["manifest"] = {"path": str(manifest_path)}
        self._last_decision = decision
        return decision

    @property
    def manifest_directory(self) -> Path:
        """Return the directory where manifests are stored."""

        return self._manifest_dir

    @property
    def latest_decision(self) -> Mapping[str, Any] | None:
        """Return the most recent orchestration decision, if available."""

        return self._last_decision

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_inputs(self) -> MutableMapping[str, Any]:
        summary = self._pulsenet.pulse_summary()
        attestations = self._pulsenet.latest_attestations(limit=8)
        atlas_wallets = []
        if hasattr(self._pulsenet, "atlas_wallets"):
            try:
                atlas_wallets = list(self._pulsenet.atlas_wallets())
            except Exception:  # pragma: no cover - defensive for offline Atlas
                atlas_wallets = []

        enriched_attestations = self._enrich_attestations(attestations)

        cycle_digest = self._evolver.cycle_digest(persist_artifact=False)

        return {
            "pulse_summary": summary,
            "attestations": enriched_attestations,
            "atlas_wallets": atlas_wallets,
            "cycle_digest": cycle_digest,
        }

    def _enrich_attestations(
        self, attestations: Sequence[Mapping[str, Any]]
    ) -> list[Mapping[str, Any]]:
        if not self._atlas_resolver:
            return list(attestations)

        enriched: list[Mapping[str, Any]] = []
        for item in attestations:
            metadata = None
            for candidate in (
                item.get("proof_id"),
                item.get("hash"),
                item.get("ref"),
            ):
                if not isinstance(candidate, str):
                    continue
                resolved = self._atlas_resolver.lookup(candidate)
                if resolved:
                    metadata = resolved.as_dict()
                    break
            payload = dict(item)
            if metadata:
                payload["atlas_metadata"] = metadata
            enriched.append(payload)
        return enriched

    def _build_resonance_seed(self, inputs: Mapping[str, Any]) -> str:
        messages: list[str] = []
        for attestation in inputs.get("attestations", []):
            pulse = attestation.get("pulse") if isinstance(attestation, Mapping) else None
            if isinstance(pulse, Mapping):
                message = pulse.get("message")
                if isinstance(message, str) and message:
                    messages.append(message)
            ref = attestation.get("ref") if isinstance(attestation, Mapping) else None
            if isinstance(ref, str) and ref:
                messages.append(ref)
        digest = inputs.get("cycle_digest", {})
        if isinstance(digest, Mapping):
            next_step = digest.get("next_step")
            if isinstance(next_step, str) and next_step:
                messages.append(next_step)
        if not messages:
            messages.append("orchestrator idle; listening for pulses")
        return " | ".join(messages)

    def _coherence_from_score(self, score: float) -> float:
        if score <= 0:
            return 0.0
        # Normalise the harmonic score into [0, 1] using a smooth logistic curve.
        return self._clamp(1.0 - math.exp(-score / 5000.0))

    def _compute_weights(
        self, inputs: Mapping[str, Any], coherence: float
    ) -> MutableMapping[str, float]:
        summary = inputs.get("pulse_summary", {})
        total_entries = float(summary.get("total_entries", 0) or 0)
        total_days = float(summary.get("total_days", 0) or 0)
        activity_rate = total_entries / total_days if total_days else 0.0
        curiosity_factor = self._normalise(activity_rate, scale=8.0)

        attestations = inputs.get("attestations", [])
        attested_count = sum(1 for _ in attestations if isinstance(_, Mapping))
        attested_ratio = attested_count / total_entries if total_entries else 0.0
        attested_ratio = min(attested_ratio, 1.0)
        noise = 1.0 - attested_ratio if total_entries else 0.0
        care_factor = 1.0 - noise

        digest = inputs.get("cycle_digest", {})
        progress = float(digest.get("progress", 0.0) or 0.0)
        continuity_factor = self._clamp(progress)

        atlas_wallets = inputs.get("atlas_wallets", [])
        atlas_factor = self._normalise(len(atlas_wallets), scale=10.0)

        weights = {
            "pulsenet": self._clamp(0.25 + 0.35 * curiosity_factor + 0.3 * coherence - 0.2 * noise),
            "resonance_field": self._clamp(0.2 + 0.6 * coherence + 0.2 * continuity_factor),
            "atlas": self._clamp(0.2 + 0.6 * care_factor + 0.2 * atlas_factor),
            "echo_evolver": self._clamp(0.3 + 0.5 * continuity_factor + 0.2 * curiosity_factor),
        }

        weights["noise"] = round(self._clamp(noise), 4)
        return weights

    def _build_graph(
        self,
        inputs: Mapping[str, Any],
        weights: Mapping[str, float],
        coherence: float,
    ) -> Mapping[str, Any]:
        summary = inputs.get("pulse_summary", {})
        digest = inputs.get("cycle_digest", {})
        attestations = inputs.get("attestations", [])

        pulsenet_status = "active" if summary.get("total_entries") else "idle"
        resonance_status = (
            "coherent"
            if coherence >= 0.6
            else "calibrating"
            if coherence >= 0.3
            else "listening"
        )
        atlas_status = "attesting" if attestations else "listening"
        evolver_status = "cycling" if (digest.get("progress", 0.0) or 0.0) < 1.0 else "ready"

        nodes = [
            {
                "id": "orchestrator",
                "label": "Orchestrator Core",
                "kind": "orchestrator",
                "weight": 1.0,
                "status": "synchronising",
            },
            {
                "id": "pulsenet",
                "label": "PulseNet",
                "kind": "module",
                "weight": weights.get("pulsenet", 0.0),
                "status": pulsenet_status,
                "metrics": summary,
            },
            {
                "id": "resonance_field",
                "label": "ResonanceField",
                "kind": "module",
                "weight": weights.get("resonance_field", 0.0),
                "status": resonance_status,
            },
            {
                "id": "atlas",
                "label": "Atlas Attestation",
                "kind": "module",
                "weight": weights.get("atlas", 0.0),
                "status": atlas_status,
            },
            {
                "id": "echo_evolver",
                "label": "EchoEvolver Cycle",
                "kind": "module",
                "weight": weights.get("echo_evolver", 0.0),
                "status": evolver_status,
                "metrics": digest,
            },
        ]

        edges = [
            {
                "source": "orchestrator",
                "target": "pulsenet",
                "strength": weights.get("pulsenet", 0.0),
                "principle": "curiosity_compass",
            },
            {
                "source": "pulsenet",
                "target": "atlas",
                "strength": weights.get("atlas", 0.0),
                "principle": "care_constraint",
            },
            {
                "source": "pulsenet",
                "target": "resonance_field",
                "strength": coherence,
                "principle": "curiosity_compass",
            },
            {
                "source": "resonance_field",
                "target": "echo_evolver",
                "strength": weights.get("echo_evolver", 0.0),
                "principle": "continuity_promise",
            },
            {
                "source": "echo_evolver",
                "target": "orchestrator",
                "strength": weights.get("echo_evolver", 0.0),
                "principle": "continuity_promise",
            },
            {
                "source": "atlas",
                "target": "orchestrator",
                "strength": weights.get("atlas", 0.0),
                "principle": "care_constraint",
            },
        ]

        return {"nodes": nodes, "edges": edges}

    def _persist(self, decision: Mapping[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc)
        filename = f"orchestration_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
        path = self._manifest_dir / filename

        payload = dict(decision)
        payload["manifest"] = {"path": str(path)}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        self._prune_manifests()
        return path

    def _prune_manifests(self) -> None:
        manifests = sorted(self._manifest_dir.glob("orchestration_*.json"))
        excess = len(manifests) - self._manifest_limit
        if excess <= 0:
            return
        for path in manifests[:excess]:
            try:
                path.unlink()
            except OSError:  # pragma: no cover - ignore filesystem race conditions
                continue

    @staticmethod
    def _normalise(value: float, *, scale: float) -> float:
        if scale <= 0:
            return 0.0
        return OrchestratorCore._clamp(value / scale)

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, float(value)))

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ["ManifestoPrinciple", "OrchestratorCore", "ResonanceEngine"]
