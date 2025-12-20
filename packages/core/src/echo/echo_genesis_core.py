"""Echo Genesis Core – unified subsystem synthesis engine.

This module weaves together quantum, telemetry, orchestration, analytics, and
governance signals into a single continually self-refining architecture view.
The :class:`EchoGenesisCore` coordinates lightweight probes for each subsystem,
tracks their evolution over time, and emits a cohesive state document that can
be used by dashboards, policy engines, and research notebooks alike.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Mapping, MutableMapping, Sequence
import json

ProbeFn = Callable[[], Mapping[str, Any] | MutableMapping[str, Any] | Any]


@dataclass(slots=True)
class SubsystemProbe:
    """Descriptor for harvesting data from a subsystem."""

    name: str
    kind: str
    focus: str
    probe: ProbeFn
    weight: float = 1.0
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class SubsystemPulse:
    """Unified snapshot derived from a subsystem probe."""

    name: str
    kind: str
    focus: str
    signal: float
    status: str
    payload: Mapping[str, Any]
    recommendations: list[str]
    delta: float


if TYPE_CHECKING:
    from .privacy.zk_layer import ProofClaim, ProofResult, ZeroKnowledgePrivacyLayer
    from .sovereign.decisions import StewardDecisionRegistry


class EchoGenesisCore:
    """Continuously evolving architecture fabric unifying Echo subsystems."""

    def __init__(
        self,
        *,
        probes: Sequence[SubsystemProbe] | None = None,
        state_dir: Path | str | None = None,
        history_limit: int = 256,
        privacy_layer: "ZeroKnowledgePrivacyLayer" | None = None,
        decision_registry: "StewardDecisionRegistry" | None = None,
    ) -> None:
        self._probes: list[SubsystemProbe] = list(probes or [])
        self._state_dir = Path(state_dir or "state/echo_genesis_core")
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._latest_path = self._state_dir / "genesis_latest.json"
        self._history_path = self._state_dir / "genesis_history.jsonl"
        self._history_limit = max(16, int(history_limit))
        self._privacy_layer = privacy_layer
        self._decision_registry = decision_registry

    # ------------------------------------------------------------------
    # Probe management
    # ------------------------------------------------------------------
    @property
    def probes(self) -> tuple[SubsystemProbe, ...]:
        """Return the registered subsystem probes."""

        return tuple(self._probes)

    def register_probe(self, probe: SubsystemProbe) -> None:
        """Register an additional subsystem probe at runtime."""

        self._probes.append(probe)

    # ------------------------------------------------------------------
    # Core synthesis loop
    # ------------------------------------------------------------------
    def synthesize(self) -> Mapping[str, Any]:
        """Collect signals from all probes and build a unified architecture."""

        if not self._probes:
            raise RuntimeError("no subsystem probes registered for EchoGenesisCore")

        previous = self._load_latest()
        pulses = [self._capture_subsystem(probe, previous) for probe in self._probes]
        analytics = self._analytics_summary(pulses)
        momentum = self._system_momentum(pulses)
        variability = self._variability(pulses)
        entanglement = self._build_entanglement(pulses)
        governance = self._governance_summary(pulses)

        refinement_index = self._refinement_index(
            analytics=analytics,
            momentum=momentum,
            variability=variability,
        )

        architecture = {
            "generated_at": self._now_iso(),
            "refinement_index": refinement_index,
            "architecture": {
                "subsystems": {
                    pulse.name: {
                        "kind": pulse.kind,
                        "focus": pulse.focus,
                        "signal": pulse.signal,
                        "status": pulse.status,
                        "payload": pulse.payload,
                        "recommendations": list(pulse.recommendations),
                        "delta": pulse.delta,
                    }
                    for pulse in pulses
                },
                "entanglement": entanglement,
            },
            "self_refinement": {
                "momentum": momentum,
                "governance": governance,
                "variability": variability,
                "analytics": analytics,
            },
            "latest_path": str(self._latest_path),
            "history_path": str(self._history_path),
        }

        privacy_snapshot = self._privacy_snapshot()
        if privacy_snapshot:
            architecture["privacy"] = privacy_snapshot

        self._persist(architecture)
        return architecture

    # ------------------------------------------------------------------
    # Privacy helpers
    # ------------------------------------------------------------------
    @property
    def privacy_layer(self) -> "ZeroKnowledgePrivacyLayer" | None:
        return self._privacy_layer

    def attach_privacy_layer(self, privacy_layer: "ZeroKnowledgePrivacyLayer") -> None:
        self._privacy_layer = privacy_layer

    def request_proof(
        self,
        circuit: str,
        claim: "ProofClaim",
        *,
        backend: str | None = None,
    ) -> "ProofResult":
        if not self._privacy_layer:
            raise RuntimeError("privacy layer not configured for EchoGenesisCore")
        return self._privacy_layer.prove(circuit, claim, backend=backend)

    def _privacy_snapshot(self) -> Mapping[str, Any]:
        if not self._privacy_layer:
            return {}
        return {
            "available_backends": self._privacy_layer.available_backends(),
            "privacy_signal": self._privacy_layer.privacy_signal(),
            "recent_commitments": self._privacy_layer.recent_commitments(limit=8),
            "receipts": self._privacy_layer.export_receipts(limit=8),
        }

    # ------------------------------------------------------------------
    # Capture + evaluation
    # ------------------------------------------------------------------
    def _capture_subsystem(
        self,
        probe: SubsystemProbe,
        previous: Mapping[str, Any] | None,
    ) -> SubsystemPulse:
        try:
            raw_payload = probe.probe()
        except Exception as exc:  # pragma: no cover - defensive catch
            payload = {"status": "error", "detail": str(exc)}
        else:
            payload = self._normalise_payload(raw_payload)

        signal = self._derive_signal(payload, probe.weight)
        status = self._status_from_signal(signal)
        recommendations = self._recommendations(signal, probe.focus)
        delta = signal - self._previous_signal(previous, probe.name)

        return SubsystemPulse(
            name=probe.name,
            kind=probe.kind,
            focus=probe.focus,
            signal=signal,
            status=status,
            payload=payload,
            recommendations=recommendations,
            delta=round(delta, 4),
        )

    def _normalise_payload(self, payload: Any) -> Mapping[str, Any]:
        def _normalise(value: Any) -> Any:
            if value is None:
                return None
            if is_dataclass(value):
                return {k: _normalise(v) for k, v in asdict(value).items()}
            if isinstance(value, Mapping):
                return {k: _normalise(v) for k, v in value.items()}
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                return [_normalise(item) for item in value]
            if hasattr(value, "to_dict"):
                try:
                    return _normalise(value.to_dict())
                except Exception:  # pragma: no cover - defensive
                    return str(value)
            if hasattr(value, "__dict__"):
                return {
                    key: _normalise(val)
                    for key, val in value.__dict__.items()
                    if not key.startswith("_")
                }
            return value

        normalized = _normalise(payload)
        if normalized is None:
            return {}
        if isinstance(normalized, Mapping):
            return dict(normalized)
        if isinstance(normalized, list):
            return {"values": normalized}
        return {"value": normalized}

    def _derive_signal(self, payload: Mapping[str, Any], weight: float) -> float:
        signal_keys = (
            "signal",
            "score",
            "stability",
            "confidence",
            "health",
            "coherence",
            "resonance",
            "momentum",
            "compliance",
        )
        candidates: list[float] = []
        for key in signal_keys:
            value = payload.get(key)
            if isinstance(value, (int, float)):
                candidates.append(float(value))
        if not candidates:
            baseline = 0.42
        else:
            baseline = sum(candidates) / len(candidates)
        scaled = baseline * weight
        return round(max(0.0, min(1.0, scaled)), 4)

    def _status_from_signal(self, signal: float) -> str:
        if signal >= 0.82:
            return "ascending"
        if signal >= 0.64:
            return "stable"
        if signal >= 0.4:
            return "recovering"
        return "dormant"

    def _recommendations(self, signal: float, focus: str) -> list[str]:
        if signal < 0.4:
            return [f"stabilize {focus}", "increase support bandwidth"]
        if signal < 0.64:
            return [f"amplify {focus}", "validate telemetry"]
        if signal < 0.82:
            return [f"sustain {focus}", "extend orchestration horizon"]
        return [f"celebrate {focus}", "propagate insights"]

    def _previous_signal(self, previous: Mapping[str, Any] | None, name: str) -> float:
        if not previous:
            return 0.0
        architecture = previous.get("architecture")
        if not isinstance(architecture, Mapping):
            return 0.0
        subsystems = architecture.get("subsystems")
        if not isinstance(subsystems, Mapping):
            return 0.0
        payload = subsystems.get(name)
        if not isinstance(payload, Mapping):
            return 0.0
        value = payload.get("signal")
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    # ------------------------------------------------------------------
    # Analytics + governance helpers
    # ------------------------------------------------------------------
    def _system_momentum(self, pulses: Sequence[SubsystemPulse]) -> Mapping[str, Any]:
        delta = round(sum(pulse.delta for pulse in pulses), 4)
        if delta > 0:
            trend = "accelerating"
        elif delta < 0:
            trend = "regressing"
        else:
            trend = "steady"
        return {
            "delta": delta,
            "trend": trend,
            "signals": {pulse.name: pulse.delta for pulse in pulses},
        }

    def _analytics_summary(self, pulses: Sequence[SubsystemPulse]) -> Mapping[str, Any]:
        if not pulses:
            return {"mean_signal": 0.0, "entropy": 0.0, "diversity": 0}
        signals = [pulse.signal for pulse in pulses]
        mean_signal = sum(signals) / len(signals)
        entropy = sum(abs(signal - mean_signal) for signal in signals) / len(signals)
        diversity = len({pulse.focus for pulse in pulses})
        return {
            "mean_signal": round(mean_signal, 4),
            "entropy": round(entropy, 4),
            "diversity": diversity,
        }

    def _variability(self, pulses: Sequence[SubsystemPulse]) -> Mapping[str, Any]:
        if not pulses:
            return {"spread": 0.0, "range": (0.0, 0.0)}
        signals = [pulse.signal for pulse in pulses]
        spread = round(max(signals) - min(signals), 4)
        return {"spread": spread, "range": (min(signals), max(signals))}

    def _build_entanglement(self, pulses: Sequence[SubsystemPulse]) -> Mapping[str, Any]:
        edges: list[Mapping[str, Any]] = []
        for index, first in enumerate(pulses):
            for second in pulses[index + 1 :]:
                weight = round((first.signal + second.signal) / 2.0, 4)
                edges.append(
                    {
                        "pair": f"{first.name}<->{second.name}",
                        "weight": weight,
                        "relationship": self._relationship(first, second),
                    }
                )
        possible_edges = max(1, len(pulses) * (len(pulses) - 1) / 2)
        density = round(len(edges) / possible_edges, 4)
        mean_weight = round(
            sum(edge["weight"] for edge in edges) / len(edges), 4
        ) if edges else 0.0
        return {"edges": edges, "density": density, "mean_weight": mean_weight}

    def _relationship(self, first: SubsystemPulse, second: SubsystemPulse) -> str:
        if first.focus == second.focus:
            return "coherent"
        if first.kind == second.kind:
            return "parallel"
        return "synergistic"

    def _governance_summary(self, pulses: Sequence[SubsystemPulse]) -> Mapping[str, Any]:
        stable = [pulse.name for pulse in pulses if pulse.status in {"ascending", "stable"}]
        escalations = [pulse.name for pulse in pulses if pulse.status in {"recovering", "dormant"}]
        summary: Dict[str, Any] = {
            "stable": stable,
            "escalate": escalations,
            "policy": {
                name: pulse.recommendations[0]
                for name, pulse in ((pulse.name, pulse) for pulse in pulses)
            },
        }
        if self._decision_registry is not None:
            summary.update(self._decision_registry.snapshot(escalations))
        return summary

    def _refinement_index(
        self,
        *,
        analytics: Mapping[str, Any],
        momentum: Mapping[str, Any],
        variability: Mapping[str, Any],
    ) -> float:
        mean_signal = float(analytics.get("mean_signal", 0.0))
        entropy = float(analytics.get("entropy", 0.0))
        delta = float(momentum.get("delta", 0.0))
        spread = float(variability.get("spread", 0.0))
        score = mean_signal + delta * 0.35 - entropy * 0.1 + spread * 0.15
        return round(max(0.0, min(1.0, score)), 4)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _persist(self, payload: Mapping[str, Any]) -> None:
        with self._latest_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        with self._history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._trim_history()

    def _load_latest(self) -> Mapping[str, Any] | None:
        if not self._latest_path.exists():
            return None
        try:
            with self._latest_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:  # pragma: no cover - corrupted state guard
            return None

    def _trim_history(self) -> None:
        if not self._history_path.exists():
            return
        lines = self._history_path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= self._history_limit:
            return
        trimmed = "\n".join(lines[-self._history_limit :]) + "\n"
        self._history_path.write_text(trimmed, encoding="utf-8")

    @property
    def latest_path(self) -> Path:
        """Path to the most recent synthesized state."""

        return self._latest_path

    @property
    def history_path(self) -> Path:
        """Path to the rolling synthesis history log."""

        return self._history_path

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Component wiring helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_components(
        cls,
        *,
        evolver: Any | None = None,
        pulsenet: Any | None = None,
        orchestrator: Any | None = None,
        analytics_engine: Any | None = None,
        governance_engine: Any | None = None,
        resonance_layer: Any | None = None,
        state_dir: Path | str | None = None,
    ) -> "EchoGenesisCore":
        probes: list[SubsystemProbe] = []

        if evolver is not None:
            def _quantum_probe(evolver: Any = evolver) -> Mapping[str, Any]:
                payload: dict[str, Any] = {}
                state = getattr(evolver, "state", None)
                if state is not None:
                    payload.update(
                        {
                            "quantum_key": getattr(state, "vault_key", None),
                            "glyphs": getattr(state, "glyphs", ""),
                            "system_metrics": self_or_dict(getattr(state, "system_metrics", {})),
                        }
                    )
                    payload["emotional_drive"] = self_or_dict(
                        getattr(state, "emotional_drive", {})
                    )
                if hasattr(evolver, "cycle_digest"):
                    try:
                        payload["cycle_digest"] = evolver.cycle_digest(persist_artifact=False)
                    except Exception:
                        payload.setdefault("errors", []).append("cycle_digest_failed")
                return payload

            probes.append(
                SubsystemProbe(
                    name="quantum",
                    kind="quantum",
                    focus="entanglement",
                    probe=_quantum_probe,
                    weight=1.05,
                )
            )

        if pulsenet is not None:
            def _telemetry_probe(pulsenet: Any = pulsenet) -> Mapping[str, Any]:
                payload: dict[str, Any] = {}
                if hasattr(pulsenet, "pulse_summary"):
                    summary = pulsenet.pulse_summary()
                    payload["summary"] = summary
                    if isinstance(summary, Mapping):
                        payload["signal"] = float(summary.get("signal", 0.6))
                if hasattr(pulsenet, "latest_attestations"):
                    payload["attestations"] = pulsenet.latest_attestations(limit=5)
                if hasattr(pulsenet, "registrations"):
                    payload["registrations"] = list(pulsenet.registrations())
                return payload

            probes.append(
                SubsystemProbe(
                    name="telemetry",
                    kind="telemetry",
                    focus="signal mesh",
                    probe=_telemetry_probe,
                    weight=0.95,
                )
            )

        if orchestrator is not None:
            def _orchestration_probe(orchestrator: Any = orchestrator) -> Mapping[str, Any]:
                decision = getattr(orchestrator, "latest_decision", None)
                if decision:
                    return decision
                if hasattr(orchestrator, "orchestrate"):
                    return orchestrator.orchestrate()
                return {}

            probes.append(
                SubsystemProbe(
                    name="orchestration",
                    kind="orchestrator",
                    focus="coordination",
                    probe=_orchestration_probe,
                    weight=1.0,
                )
            )

        if analytics_engine is not None:
            def _analytics_probe(engine: Any = analytics_engine) -> Mapping[str, Any]:
                if hasattr(engine, "snapshot"):
                    return engine.snapshot()
                if hasattr(engine, "summary"):
                    return engine.summary()
                if hasattr(engine, "to_dict"):
                    return engine.to_dict()
                return {"signal": 0.6}

            probes.append(
                SubsystemProbe(
                    name="analytics",
                    kind="analytics",
                    focus="insights",
                    probe=_analytics_probe,
                    weight=1.0,
                )
            )

        if governance_engine is not None:
            def _governance_probe(engine: Any = governance_engine) -> Mapping[str, Any]:
                state = getattr(engine, "state", None)
                if isinstance(state, Mapping):
                    return dict(state)
                if hasattr(engine, "to_dict"):
                    return engine.to_dict()
                return {"compliance": 0.7}

            probes.append(
                SubsystemProbe(
                    name="governance",
                    kind="governance",
                    focus="policy",
                    probe=_governance_probe,
                    weight=0.9,
                )
            )

        if resonance_layer is not None:
            def _resonance_probe(layer: Any = resonance_layer) -> Mapping[str, Any]:
                if hasattr(layer, "snapshot"):
                    return layer.snapshot()
                if hasattr(layer, "state"):
                    return self_or_dict(layer.state)
                return {"signal": 0.5, "status": "unknown"}

            probes.append(
                SubsystemProbe(
                    name="resonance",
                    kind="continuum",
                    focus="coherence",
                    probe=_resonance_probe,
                    weight=1.05,
                )
            )

        return cls(probes=probes, state_dir=state_dir)


def self_or_dict(value: Any) -> Mapping[str, Any]:
    """Normalise optional value into a mapping for serialization."""

    if value is None:
        return {}
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:  # pragma: no cover - helper guard
            return {"value": str(value)}
    if hasattr(value, "__dict__"):
        return {
            key: val
            for key, val in value.__dict__.items()
            if not key.startswith("_") and isinstance(val, (int, float, str, bool, list, dict))
        }
    return {"value": value}


__all__ = ["EchoGenesisCore", "SubsystemProbe", "SubsystemPulse"]
