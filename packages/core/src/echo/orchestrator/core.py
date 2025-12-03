"""Orchestrator core that unifies PulseNet, ResonanceField, Atlas, and EchoEvolver."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, MutableMapping, Optional, Protocol, Sequence

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from echo.bridge.service import BridgeSyncService

from echo.bank.resilience import ResilienceRecorder
from echo.evolver import EchoEvolver
from echo.pulsenet import AtlasAttestationResolver, PulseNetGatewayService
from echo.orchestrator.persistence import LocalOrchestratorStore
from echo.semantic_negotiation import (
    NegotiationIntent,
    NegotiationParticipant,
    NegotiationSignal,
    NegotiationStage,
    SemanticNegotiationResolver,
)
from governance.persistence import load_policies, load_roles, log_action


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


def enforce_governance(actor: str, action: str) -> None:
    policies = load_policies()
    roles = load_roles()

    # block actions requiring signoff
    if action in policies.get("requires_signoff", []):
        if actor != roles.get("AI_GOV_LEAD"):
            log_action(actor, action, {"blocked": True})
            raise PermissionError(f"Action '{action}' requires signoff")

    log_action(actor, action, {"blocked": False})


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
        bridge_service: "BridgeSyncService" | None = None,
        resilience_latest_path: Path | str | None = None,
        resilience_interval_hours: float = 72.0,
        resilience_cooldown_hours: float = 6.0,
        negotiation_resolver: SemanticNegotiationResolver | None = None,
        offline_cache_ttl_hours: float | None = 48.0,
        allow_stale_offline_cache: bool = True,
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
        self._negotiations = negotiation_resolver
        self._offline_cache_path = self._state_dir / "offline_cache.json"
        self._offline_cache_ttl = (
            timedelta(hours=max(0.0, float(offline_cache_ttl_hours)))
            if offline_cache_ttl_hours is not None
            else None
        )
        self._allow_stale_offline_cache = allow_stale_offline_cache

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
        self._bridge_service = bridge_service
        self._resilience_latest = (
            Path(resilience_latest_path)
            if resilience_latest_path is not None
            else Path("state/resilience/latest.json")
        )
        self._resilience_drill_log = self._state_dir / "resilience_drills.jsonl"
        self._resilience_interval = timedelta(hours=max(1.0, float(resilience_interval_hours)))
        self._resilience_cooldown = timedelta(hours=max(0.5, float(resilience_cooldown_hours)))
        self._store = LocalOrchestratorStore(self._state_dir / "orchestrator_state.db")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def orchestrate(self) -> Mapping[str, Any]:
        """Collect module outputs, derive adaptive weights, and persist a manifest."""

        offline_mode = False
        offline_reason: str | None = None
        offline_details: MutableMapping[str, Any] | None = None
        active_policy_version = self._store.get_active_policy_version()
        request_id = self._store.log_request(
            {"kind": "orchestration", "requested_at": self._now_iso()}
        )
        try:
            inputs = self._collect_inputs()
            self._persist_offline_cache(inputs)
        except Exception as exc:  # pragma: no cover - defensive offline fallback
            offline_mode = True
            offline_reason = str(exc)
            cached = self._load_offline_cache()
            if not cached:
                raise
            inputs, offline_details = cached
            if offline_details is None:
                offline_details = {}
            cache_stale = offline_details.get("cache_stale")
            if cache_stale and not self._allow_stale_offline_cache:
                raise RuntimeError(
                    "stale offline cache refused; enable allow_stale_offline_cache to use it"
                ) from exc
            offline_details.setdefault("offline_used", True)
            offline_details.setdefault("offline_reason", offline_reason)
            offline_details.setdefault("offline_policy_version", active_policy_version)
            offline_details.setdefault("offline_source", str(self._offline_cache_path))
            snapshot = offline_details.get("policy_snapshot")
            if not offline_details.get("offline_policy_version") and isinstance(
                snapshot, Sequence
            ):
                policy_hint = next((item for item in snapshot if isinstance(item, Mapping)), None)
                if policy_hint:
                    policy_id = policy_hint.get("policy_id")
                    version = policy_hint.get("version")
                    if isinstance(policy_id, str) and isinstance(version, (int, str)):
                        offline_details["offline_policy_version"] = f"{policy_id}@v{version}"
            logging.warning("Orchestrator using offline cache after error: %s", exc)
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
        decision["offline_mode"] = offline_mode
        if offline_details:
            decision["offline_details"] = offline_details
        if active_policy_version:
            decision["active_policy_version"] = active_policy_version

        momentum = self._evaluate_momentum(inputs, coherence, weights)
        decision["momentum"] = momentum
        if momentum["triggers"]:
            decision["triggers"] = list(momentum["triggers"])

        resilience_plan = self._plan_resilience(inputs.get("resilience_snapshot"))
        decision["resilience"] = resilience_plan
        triggers = list(decision.get("triggers", []))
        if resilience_plan.get("scheduled_for"):
            reason = "; ".join(resilience_plan.get("reasons", [])) or "Resilience drill scheduled"
            triggers.append(
                {
                    "id": "resilience_drill",
                    "kind": "resilience",
                    "action": "run_resilience_drill",
                    "reason": reason,
                    "scheduled_for": resilience_plan["scheduled_for"],
                }
            )
        if triggers:
            decision["triggers"] = triggers

        if self._negotiations:
            decision["negotiations"] = inputs.get("negotiations", {})

        manifest_path = self._persist(decision)
        decision["manifest"] = {"path": str(manifest_path)}

        if self._bridge_service:
            try:
                operations = self._bridge_service.sync(decision)
                bridge_payload: MutableMapping[str, Any] = {
                    "operations": operations,
                    "log_path": str(self._bridge_service.log_path),
                }
            except Exception as exc:  # pragma: no cover - defensive against I/O errors
                bridge_payload = {
                    "operations": [],
                    "log_path": str(self._bridge_service.log_path),
                    "error": str(exc),
                }
            decision["bridge_sync"] = bridge_payload
        offline_policy_version = (
            decision.get("offline_details", {}).get("offline_policy_version")
            if offline_mode
            else active_policy_version
        )
        self._store.log_decision(
            request_id,
            decision,
            offline_mode=offline_mode,
            offline_reason=offline_reason,
            offline_policy_version=offline_policy_version,
        )
        self._store.record_metric(
            "coherence_score",
            harmonic_score,
            metadata={"timestamp": decision["timestamp"], "offline": offline_mode},
        )
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

    def initiate_negotiation(
        self,
        intent: NegotiationIntent,
        participants: Sequence[NegotiationParticipant],
        *,
        actor: str = "system",
        metadata: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Open a new semantic negotiation and return its state."""

        if not self._negotiations:
            raise RuntimeError("semantic negotiation resolver not configured")
        state = self._negotiations.initiate(
            intent=intent,
            participants=participants,
            actor=actor,
            metadata=metadata,
        )
        return state.model_dump(mode="json")

    def update_negotiation_stage(
        self,
        negotiation_id: str,
        stage: NegotiationStage,
        *,
        actor: str,
        reason: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Transition a negotiation to a new stage."""

        if not self._negotiations:
            raise RuntimeError("semantic negotiation resolver not configured")
        state = self._negotiations.transition(
            negotiation_id,
            stage,
            actor=actor,
            reason=reason,
            metadata=metadata,
        )
        return state.model_dump(mode="json")

    def record_negotiation_signal(
        self,
        negotiation_id: str,
        *,
        author: str,
        channel: str,
        sentiment: float | None = None,
        summary: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Attach an observational signal to an active negotiation."""

        if not self._negotiations:
            raise RuntimeError("semantic negotiation resolver not configured")
        signal = NegotiationSignal(
            author=author,
            channel=channel,
            sentiment=sentiment,
            summary=summary,
            payload=dict(payload or {}),
        )
        state = self._negotiations.record_signal(negotiation_id, signal)
        return state.model_dump(mode="json")

    def negotiation_snapshot(self, include_closed: bool = False) -> Mapping[str, Any]:
        """Return a snapshot of negotiations suitable for dashboards."""

        if not self._negotiations:
            return {"enabled": False, "observations": []}
        snapshot = self._negotiations.snapshot(include_closed=include_closed)
        data = snapshot.model_dump(mode="json")
        data["enabled"] = True
        return data

    def negotiation_metrics(self) -> Mapping[str, Any]:
        """Expose aggregate negotiation metrics."""

        if not self._negotiations:
            return {"enabled": False, "metrics": {}}
        return {"enabled": True, "metrics": self._negotiations.metrics()}

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

        registrations: Sequence[Mapping[str, Any]] = []
        if hasattr(self._pulsenet, "registrations"):
            try:
                raw_regs = self._pulsenet.registrations()  # type: ignore[call-arg]
                if isinstance(raw_regs, Sequence):
                    registrations = [
                        item for item in raw_regs if isinstance(item, Mapping)
                    ]
            except Exception:  # pragma: no cover - tolerate offline registration store
                registrations = []

        resilience_snapshot = self._load_resilience_snapshot()

        inputs: MutableMapping[str, Any] = {
            "pulse_summary": summary,
            "attestations": enriched_attestations,
            "atlas_wallets": atlas_wallets,
            "cycle_digest": cycle_digest,
            "registrations": list(registrations),
            "resilience_snapshot": resilience_snapshot.to_payload() if resilience_snapshot else None,
        }
        if self._negotiations:
            inputs["negotiations"] = self._negotiations.snapshot().model_dump(mode="json")
        return inputs

    def _persist_offline_cache(self, inputs: Mapping[str, Any]) -> None:
        payload = {
            "cached_at": self._now_iso(),
            "inputs": inputs,
            "offline_state": self._store.snapshot_state(),
            "cache_ttl_hours": self._offline_cache_ttl.total_seconds() / 3600
            if self._offline_cache_ttl
            else None,
        }
        try:
            serialised = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
            self._offline_cache_path.write_text(serialised)
        except Exception as exc:  # pragma: no cover - best-effort cache
            logging.debug("Unable to persist offline cache: %s", exc)

    def _load_offline_cache(self) -> tuple[MutableMapping[str, Any], MutableMapping[str, Any]] | None:
        if not self._offline_cache_path.exists():
            return None
        try:
            data = json.loads(self._offline_cache_path.read_text())
        except Exception as exc:  # pragma: no cover - corrupted cache
            logging.warning("Offline cache unreadable: %s", exc)
            return None

        inputs = data.get("inputs") if isinstance(data, Mapping) else None
        if not isinstance(inputs, Mapping):
            return None

        cached_at = data.get("cached_at") if isinstance(data, Mapping) else None
        details: MutableMapping[str, Any] = {"cache_path": str(self._offline_cache_path)}
        if isinstance(cached_at, str):
            details["cached_at"] = cached_at
            parsed = self._parse_iso(cached_at)
            if parsed:
                age = datetime.now(timezone.utc) - parsed
                details["cache_age_seconds"] = max(0.0, age.total_seconds())
                if self._offline_cache_ttl:
                    ttl_seconds = self._offline_cache_ttl.total_seconds()
                    details["cache_ttl_seconds"] = ttl_seconds
                    details["cache_stale"] = age > self._offline_cache_ttl
        offline_state = data.get("offline_state") if isinstance(data, Mapping) else None
        if isinstance(offline_state, Mapping):
            if offline_state.get("policies"):
                details["policy_snapshot"] = offline_state.get("policies")
            if offline_state.get("config"):
                details["config_snapshot"] = offline_state.get("config")
            if offline_state.get("metrics"):
                details["metrics_snapshot"] = offline_state.get("metrics")
        return dict(inputs), details

    def offline_status(self) -> Mapping[str, Any]:
        """Return metadata about the offline cache for diagnostics and UIs."""

        status: MutableMapping[str, Any] = {
            "path": str(self._offline_cache_path),
            "exists": self._offline_cache_path.exists(),
        }

        if not status["exists"]:
            return status

        try:
            data = json.loads(self._offline_cache_path.read_text())
        except Exception as exc:  # pragma: no cover - defensive metadata read
            status["error"] = str(exc)
            return status

        cached_at = data.get("cached_at") if isinstance(data, Mapping) else None
        if isinstance(cached_at, str):
            status["cached_at"] = cached_at
            parsed = self._parse_iso(cached_at)
            if parsed:
                age = datetime.now(timezone.utc) - parsed
                status["cache_age_seconds"] = max(0.0, age.total_seconds())
                if self._offline_cache_ttl:
                    status["cache_ttl_seconds"] = self._offline_cache_ttl.total_seconds()
                    status["cache_stale"] = age > self._offline_cache_ttl
        status["has_inputs"] = isinstance(data.get("inputs"), Mapping)

        offline_state = data.get("offline_state") if isinstance(data, Mapping) else None
        if isinstance(offline_state, Mapping):
            status["offline_state_keys"] = sorted(offline_state.keys())

        return status

    def offline_readiness(self) -> Mapping[str, Any]:
        """Summarise offline readiness and highlight missing artefacts."""

        status = self.offline_status()
        manifests = sorted(self._manifest_dir.glob("orchestration_*.json"))
        latest_manifest = manifests[-1] if manifests else None
        actions: list[str] = []

        manifest_age_seconds: float | None = None
        if latest_manifest:
            try:
                mtime = datetime.fromtimestamp(
                    latest_manifest.stat().st_mtime, tz=timezone.utc
                )
                manifest_age_seconds = max(
                    0.0, (datetime.now(timezone.utc) - mtime).total_seconds()
                )
            except Exception:
                manifest_age_seconds = None

        if not status.get("exists"):
            actions.append("Seed offline cache by running orchestrate() at least once.")
        if status.get("cache_stale"):
            actions.append("Refresh offline cache before offline use (cache is stale).")
        if not manifests:
            actions.append("Generate at least one manifest for offline replay.")
        if self._last_decision is None:
            actions.append("Capture a decision snapshot by running orchestrate().")

        readiness: MutableMapping[str, Any] = {
            "ready": not actions,
            "cache_status": status,
            "manifest_count": len(manifests),
            "latest_manifest": str(latest_manifest) if latest_manifest else None,
            "latest_manifest_age_seconds": manifest_age_seconds,
            "pending_actions": actions,
        }

        return readiness

    def purge_offline_cache(self) -> bool:
        """Remove the offline cache from disk to force a refresh on next run."""

        if not self._offline_cache_path.exists():
            return False

        try:
            self._offline_cache_path.unlink()
            return True
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logging.debug("Unable to purge offline cache: %s", exc)
            return False

    def export_offline_bundle(self, path: Path | str | None = None) -> Mapping[str, Any]:
        """Persist an offline-ready bundle with cache inputs and state snapshots.

        The bundle stitches together the current offline cache (if any), a
        fresh snapshot from the local store, the most recent manifest path, and
        the last in-memory decision. It is designed for environments that need
        to ship diagnostics or replay orchestration inputs without network
        access.
        """

        target = Path(path) if path is not None else self._state_dir / "offline_bundle.json"
        target.parent.mkdir(parents=True, exist_ok=True)

        status = self.offline_status()
        cache_payload: MutableMapping[str, Any] = {}
        if status.get("exists"):
            try:
                raw_cache = json.loads(self._offline_cache_path.read_text())
                if isinstance(raw_cache, Mapping):
                    cache_payload.update(raw_cache)
            except Exception as exc:  # pragma: no cover - defensive read
                cache_payload["cache_error"] = str(exc)

        manifests = sorted(self._manifest_dir.glob("orchestration_*.json"))
        latest_manifest = str(manifests[-1]) if manifests else None

        bundle: MutableMapping[str, Any] = {
            "generated_at": self._now_iso(),
            "status": status,
            "cache_metadata": {
                key: cache_payload.get(key)
                for key in ("cached_at", "cache_ttl_hours", "cache_error")
                if cache_payload.get(key) is not None
            },
            "inputs": cache_payload.get("inputs"),
            "offline_state": cache_payload.get("offline_state")
            if cache_payload.get("offline_state") is not None
            else self._store.snapshot_state(),
            "latest_manifest": latest_manifest,
            "last_decision": self._last_decision,
            "readiness": self.offline_readiness(),
        }

        target.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))
        bundle["path"] = str(target)
        return bundle

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

    def _evaluate_momentum(
        self,
        inputs: Mapping[str, Any],
        coherence: float,
        weights: Mapping[str, float],
    ) -> MutableMapping[str, Any]:
        digest = inputs.get("cycle_digest", {})
        progress = 0.0
        if isinstance(digest, Mapping):
            progress = float(digest.get("progress", 0.0) or 0.0)

        prev_progress = progress
        prev_coherence = coherence
        if isinstance(self._last_decision, Mapping):
            previous_inputs = self._last_decision.get("inputs")
            if isinstance(previous_inputs, Mapping):
                previous_digest = previous_inputs.get("cycle_digest")
                if isinstance(previous_digest, Mapping):
                    prev_progress = float(previous_digest.get("progress", 0.0) or 0.0)
            previous_coherence_payload = self._last_decision.get("coherence")
            if isinstance(previous_coherence_payload, Mapping):
                prev_score = previous_coherence_payload.get("score")
                if isinstance(prev_score, (int, float)):
                    prev_coherence = self._coherence_from_score(float(prev_score))

        delta_progress = progress - prev_progress
        delta_coherence = coherence - prev_coherence

        summary = inputs.get("pulse_summary", {})
        total_entries = 0.0
        if isinstance(summary, Mapping):
            total_entries = float(summary.get("total_entries", 0) or 0)
        attestations = inputs.get("attestations", [])
        attested_count = sum(1 for item in attestations if isinstance(item, Mapping))
        attested_ratio = attested_count / total_entries if total_entries else 0.0
        attested_ratio = self._clamp(attested_ratio)

        positive_delta = max(delta_progress, 0.0)
        negative_delta = max(-delta_progress, 0.0)
        momentum_score = self._clamp(
            0.5 * positive_delta + 0.3 * coherence + 0.2 * attested_ratio
        )
        slump_score = self._clamp(
            0.5 * negative_delta + 0.3 * (1.0 - coherence) + 0.2 * (1.0 - attested_ratio)
        )

        triggers: list[dict[str, Any]] = []
        if positive_delta >= 0.05 and momentum_score >= 0.6:
            triggers.append(
                {
                    "id": "momentum_surge",
                    "kind": "momentum",
                    "action": "accelerate_cycle",
                    "reason": f"progress advanced {delta_progress:.2f}",
                    "momentum": self._round(momentum_score),
                }
            )
        if (negative_delta >= 0.05 or coherence < 0.25) and slump_score >= 0.5:
            if negative_delta >= 0.05:
                detail = f"progress regressed {negative_delta:.2f}"
            else:
                detail = "coherence dipped below 0.25"
            triggers.append(
                {
                    "id": "momentum_stall",
                    "kind": "momentum",
                    "action": "stabilise_cycle",
                    "reason": detail,
                    "momentum": self._round(slump_score),
                }
            )

        return {
            "progress": self._round(progress),
            "previous_progress": self._round(prev_progress),
            "delta_progress": self._round(delta_progress),
            "coherence": self._round(coherence),
            "previous_coherence": self._round(prev_coherence),
            "delta_coherence": self._round(delta_coherence),
            "attested_ratio": self._round(attested_ratio),
            "score": self._round(momentum_score),
            "slump": self._round(slump_score),
            "triggers": triggers,
        }

    def _persist(self, decision: Mapping[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc)
        filename = f"orchestration_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
        path = self._manifest_dir / filename

        payload = dict(decision)
        payload["manifest"] = {"path": str(path)}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        self._prune_manifests()
        return path

    def _load_resilience_snapshot(self) -> "ResilienceSnapshot | None":
        return ResilienceRecorder.load_latest_snapshot(self._resilience_latest)

    def _plan_resilience(
        self, snapshot_payload: Mapping[str, Any] | None
    ) -> MutableMapping[str, Any]:
        now = datetime.now(timezone.utc)
        plan: MutableMapping[str, Any] = {
            "snapshot": snapshot_payload,
            "failover_ready": None,
            "healthy_mirrors": None,
            "total_mirrors": None,
            "recorded_at": None,
            "issues": [],
            "scheduled_for": None,
            "reasons": [],
            "last_drill": None,
            "cooldown_active": False,
        }

        recorded_at = None
        issues: list[str] = []
        failover_ready: Optional[bool] = None
        healthy_mirrors: Optional[int] = None
        total_mirrors: Optional[int] = None
        if isinstance(snapshot_payload, Mapping):
            failover_ready = bool(snapshot_payload.get("failover_ready", False))
            healthy_mirrors = (
                int(snapshot_payload.get("healthy_mirrors", 0))
                if snapshot_payload.get("healthy_mirrors") is not None
                else None
            )
            total_mirrors = (
                int(snapshot_payload.get("total_mirrors", 0))
                if snapshot_payload.get("total_mirrors") is not None
                else None
            )
            issues_payload = snapshot_payload.get("issues")
            if isinstance(issues_payload, Sequence):
                issues = [str(entry) for entry in issues_payload]
            recorded_at = self._parse_iso(snapshot_payload.get("recorded_at"))
            plan["recorded_at"] = snapshot_payload.get("recorded_at")
        else:
            plan["recorded_at"] = None

        plan["failover_ready"] = failover_ready
        plan["healthy_mirrors"] = healthy_mirrors
        plan["total_mirrors"] = total_mirrors
        plan["issues"] = issues

        reasons: list[str] = []
        due = False
        if snapshot_payload is None:
            due = True
            reasons.append("No resilience snapshot available")
        else:
            if failover_ready is False:
                due = True
                reasons.append("Failover mirrors are not ready")
            if recorded_at is None:
                due = True
                reasons.append("Resilience snapshot timestamp unavailable")
            else:
                age = now - recorded_at
                if age >= self._resilience_interval:
                    hours = age.total_seconds() / 3600.0
                    reasons.append(f"Last resilience snapshot is {hours:.1f} hours old")
                    due = True
            for issue in issues:
                reasons.append(f"Issue: {issue}")

        last_drill = self._load_last_drill()
        if last_drill is not None:
            plan["last_drill"] = last_drill.get("scheduled_for")
            last_time = self._parse_iso(last_drill.get("scheduled_for"))
            if last_time is not None and now - last_time < self._resilience_cooldown:
                plan["cooldown_active"] = True
                if due:
                    reasons.append("Cooldown active — drill recently scheduled")
                due = False

        plan["reasons"] = reasons
        if due:
            scheduled_for = now.isoformat()
            plan["scheduled_for"] = scheduled_for
            self._record_resilience_drill(now, reasons, snapshot_payload)

        return plan

    def _load_last_drill(self) -> Mapping[str, Any] | None:
        if not self._resilience_drill_log.exists():
            return None
        lines = self._resilience_drill_log.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                return payload
        return None

    def _record_resilience_drill(
        self,
        scheduled_for: datetime,
        reasons: Sequence[str],
        snapshot_payload: Mapping[str, Any] | None,
    ) -> None:
        record: MutableMapping[str, Any] = {
            "scheduled_for": scheduled_for.isoformat(),
            "logged_at": self._now_iso(),
            "reasons": list(reasons),
        }
        if isinstance(snapshot_payload, Mapping):
            if "seq" in snapshot_payload:
                record["snapshot_seq"] = snapshot_payload["seq"]
            if "digest" in snapshot_payload:
                record["snapshot_digest"] = snapshot_payload["digest"]
        with self._resilience_drill_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

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
    def _round(value: float, digits: int = 4) -> float:
        return float(round(float(value), digits))

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _parse_iso(value: Any) -> Optional[datetime]:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


__all__ = ["ManifestoPrinciple", "OrchestratorCore", "ResonanceEngine"]
