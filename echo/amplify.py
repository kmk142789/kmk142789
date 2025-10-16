"""Amplification analytics for the Echo evolver.

This module introduces a deterministic amplification engine capable of
measuring creative momentum across evolver cycles.  The metrics are kept
deliberately simple – they only rely on the public ``EvolverState``
interface and avoid hidden randomness so that identical repository state
always yields identical amplification results.  The design favours
testability: dependency injection points allow tests to supply fixed time
and commit sources while the metric helpers are implemented as pure
functions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .thoughtlog import thought_trace


def _clamp(value: float, *, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _safe_round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


@dataclass(frozen=True)
class AmplifyMetrics:
    """Individual metric components for an amplification snapshot."""

    resonance: float
    freshness_half_life: float
    novelty_delta: float
    cohesion: float
    coverage: float
    stability: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "resonance": self.resonance,
            "freshness_half_life": self.freshness_half_life,
            "novelty_delta": self.novelty_delta,
            "cohesion": self.cohesion,
            "coverage": self.coverage,
            "stability": self.stability,
        }


@dataclass(frozen=True)
class AmplifySnapshot:
    """Deterministic artefact capturing cycle metrics."""

    cycle: int
    metrics: AmplifyMetrics
    index: float
    timestamp: str
    commit_sha: str

    def as_dict(self) -> Dict[str, object]:
        payload = {
            "cycle": self.cycle,
            "metrics": self.metrics.as_dict(),
            "index": self.index,
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
        }
        return payload


@dataclass(slots=True)
class AmplifyThresholds:
    """Configuration for metric nudges."""

    resonance: float = 60.0
    freshness_half_life: float = 55.0
    novelty_delta: float = 50.0
    cohesion: float = 50.0
    coverage: float = 65.0
    stability: float = 60.0


@dataclass(slots=True)
class AmplifyWeights:
    """Weight profile used when calculating the composite index."""

    resonance: float = 0.24
    freshness: float = 0.16
    novelty: float = 0.18
    cohesion: float = 0.16
    coverage: float = 0.14
    volatility: float = 0.12


@dataclass(slots=True)
class AmplifyState:
    """Minimal view of data required to compute amplification metrics."""

    cycle: int
    joy: float
    curiosity: float
    rage: float
    completed_steps: int
    expected_steps: int
    mythocode_count: int
    propagation_channels: int
    events: int
    network_nodes: int
    orbital_hops: int

    @classmethod
    def from_evolver(cls, state: object, *, expected_steps: int) -> "AmplifyState":
        completed = getattr(state, "network_cache", {}).get("completed_steps", set())
        mythocode = getattr(state, "mythocode", [])
        propagation = getattr(state, "network_cache", {}).get("propagation_events", [])
        events = getattr(state, "event_log", [])
        metrics = getattr(state, "system_metrics", None)
        if metrics is None:
            nodes = 0
            hops = 0
        else:
            nodes = getattr(metrics, "network_nodes", 0)
            hops = getattr(metrics, "orbital_hops", 0)
        emotions = getattr(state, "emotional_drive", None)
        joy = getattr(emotions, "joy", 0.0)
        curiosity = getattr(emotions, "curiosity", 0.0)
        rage = getattr(emotions, "rage", 0.0)
        return cls(
            cycle=getattr(state, "cycle", 0),
            joy=float(joy),
            curiosity=float(curiosity),
            rage=float(rage),
            completed_steps=len(completed) if isinstance(completed, Iterable) else 0,
            expected_steps=expected_steps,
            mythocode_count=len(mythocode) if isinstance(mythocode, Sequence) else 0,
            propagation_channels=len(propagation) if isinstance(propagation, Sequence) else 0,
            events=len(events) if isinstance(events, Sequence) else 0,
            network_nodes=int(nodes),
            orbital_hops=int(hops),
        )


class AmplifyGateError(RuntimeError):
    """Raised when the rolling amplification average does not meet a gate."""


class AmplificationEngine:
    """High level orchestration for amplification metrics and persistence."""

    def __init__(
        self,
        *,
        thresholds: AmplifyThresholds | None = None,
        weights: AmplifyWeights | None = None,
        time_source: callable | None = None,
        commit_source: callable | None = None,
        log_path: Path | str | None = None,
        manifest_path: Path | str | None = None,
    ) -> None:
        self.thresholds = thresholds or AmplifyThresholds()
        self.weights = weights or AmplifyWeights()
        self.time_source = time_source or (lambda: datetime.now(tz=timezone.utc))
        self.commit_source = commit_source or self._resolve_commit
        self.log_path = Path(log_path) if log_path else Path("state/amplify_log.jsonl")
        self.manifest_path = (
            Path(manifest_path) if manifest_path else Path("echo_manifest.json")
        )
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Metric computation
    # ------------------------------------------------------------------
    def compute_metrics(
        self,
        state: AmplifyState,
        previous: AmplifySnapshot | None,
    ) -> AmplifyMetrics:
        joy = _clamp(state.joy * 100.0)
        curiosity = _clamp(state.curiosity * 100.0)
        rage = _clamp(state.rage * 100.0)

        resonance = _clamp(0.6 * joy + 0.4 * (100 - rage))

        decay_cycles = 0 if previous is None else state.cycle - previous.cycle
        freshness = _clamp(100.0 * math.exp(-0.15 * max(decay_cycles, 0)))

        previous_mythocode = (
            previous.metrics.novelty_delta
            if previous is not None and previous.cycle < state.cycle
            else 0.0
        )
        novelty_base = state.mythocode_count * 18.0
        novelty_delta = _clamp(novelty_base + 0.35 * (curiosity - rage) - previous_mythocode * 0.1)

        cohesion = _clamp(70 + 0.3 * (joy + curiosity) - 0.4 * rage)

        completion_ratio = state.completed_steps / max(1, state.expected_steps)
        coverage = _clamp(completion_ratio * 100.0)

        signal = (state.events + state.propagation_channels) / max(1, state.cycle or 1)
        volatility = _clamp(min(100.0, signal * 12.0))
        stability = _clamp(100.0 - 0.6 * volatility)

        metrics = AmplifyMetrics(
            resonance=_safe_round(resonance),
            freshness_half_life=_safe_round(freshness),
            novelty_delta=_safe_round(novelty_delta),
            cohesion=_safe_round(cohesion),
            coverage=_safe_round(coverage),
            stability=_safe_round(stability),
        )
        return metrics

    def compute_index(self, metrics: AmplifyMetrics) -> float:
        volatility = 100.0 - metrics.stability
        index = (
            self.weights.resonance * metrics.resonance
            + self.weights.freshness * metrics.freshness_half_life
            + self.weights.novelty * metrics.novelty_delta
            + self.weights.cohesion * metrics.cohesion
            + self.weights.coverage * metrics.coverage
            - self.weights.volatility * volatility
        )
        return _safe_round(_clamp(index))

    def build_snapshot(
        self,
        state: AmplifyState,
        *,
        previous: AmplifySnapshot | None,
    ) -> AmplifySnapshot:
        metrics = self.compute_metrics(state, previous)
        index = self.compute_index(metrics)
        commit_sha = str(self.commit_source()).strip()
        if (
            previous
            and previous.cycle == state.cycle
            and previous.commit_sha == commit_sha
            and previous.index == index
            and previous.metrics.as_dict() == metrics.as_dict()
        ):
            timestamp = previous.timestamp
        else:
            timestamp = self._format_timestamp(self.time_source())
        snapshot = AmplifySnapshot(
            cycle=state.cycle,
            metrics=metrics,
            index=index,
            timestamp=timestamp,
            commit_sha=commit_sha,
        )
        return snapshot

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def load_history(self) -> List[AmplifySnapshot]:
        history: List[AmplifySnapshot] = []
        if not self.log_path.exists():
            return history

        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                metrics_payload = payload["metrics"]
                metrics = AmplifyMetrics(
                    resonance=float(metrics_payload["resonance"]),
                    freshness_half_life=float(metrics_payload["freshness_half_life"]),
                    novelty_delta=float(metrics_payload["novelty_delta"]),
                    cohesion=float(metrics_payload["cohesion"]),
                    coverage=float(metrics_payload["coverage"]),
                    stability=float(metrics_payload["stability"]),
                )
                history.append(
                    AmplifySnapshot(
                        cycle=int(payload["cycle"]),
                        metrics=metrics,
                        index=float(payload["index"]),
                        timestamp=str(payload["timestamp"]),
                        commit_sha=str(payload["commit_sha"]),
                    )
                )
        return history

    def persist_snapshot(self, snapshot: AmplifySnapshot) -> None:
        history = self.load_history()
        if history and history[-1].as_dict() == snapshot.as_dict():
            return
        with self.log_path.open("a", encoding="utf-8") as handle:
            json.dump(snapshot.as_dict(), handle, sort_keys=True)
            handle.write("\n")

    def update_manifest(self, snapshot: AmplifySnapshot) -> None:
        if not self.manifest_path.exists():
            return

        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        rolling = self.rolling_average(window=3)
        amplification = {
            "latest": snapshot.index,
            "rolling_avg": rolling,
            "gate": {
                "weights": asdict(self.weights),
                "thresholds": asdict(self.thresholds),
            },
        }
        data["amplification"] = amplification
        self.manifest_path.write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def before_cycle(self, state: object, *, expected_steps: int) -> None:
        task = "amplify.before_cycle"
        with thought_trace(task=task, meta={"cycle": getattr(state, "cycle", 0)}):
            # No-op hook retained for symmetry; reserved for future use.
            pass

    def after_cycle(self, state: object, *, expected_steps: int) -> Tuple[AmplifySnapshot, List[str]]:
        history = self.load_history()
        previous = history[-1] if history else None
        amplify_state = AmplifyState.from_evolver(state, expected_steps=expected_steps)
        snapshot = self.build_snapshot(amplify_state, previous=previous)
        nudges = self._generate_nudges(snapshot.metrics)
        self.persist_snapshot(snapshot)
        self.update_manifest(snapshot)
        return snapshot, nudges

    # ------------------------------------------------------------------
    # Derived data
    # ------------------------------------------------------------------
    def rolling_average(self, *, window: int = 3) -> Optional[float]:
        history = self.load_history()
        if not history:
            return None
        relevant = history[-window:]
        if not relevant:
            return None
        return _safe_round(sum(item.index for item in relevant) / len(relevant))

    def require_gate(self, *, minimum: float, window: int = 3) -> None:
        average = self.rolling_average(window=window)
        if average is None or average < minimum:
            raise AmplifyGateError(
                f"Amplify gate minimum {minimum} not met (rolling average {average})"
            )

    def _generate_nudges(self, metrics: AmplifyMetrics) -> List[str]:
        nudges: List[str] = []
        if metrics.novelty_delta < self.thresholds.novelty_delta:
            nudges.append("Low novelty: mutate rule space with mythocode shuffle.")
        if metrics.cohesion < self.thresholds.cohesion:
            nudges.append("Cohesion drop: run refactor pass on narrative threads.")
        if metrics.coverage < self.thresholds.coverage:
            nudges.append("Coverage sag: ensure full cycle sequence executed.")
        if metrics.resonance < self.thresholds.resonance:
            nudges.append("Resonance weak: boost joy inputs before next cycle.")
        if metrics.freshness_half_life < self.thresholds.freshness_half_life:
            nudges.append("Freshness fading: inject new prompts or datasets.")
        if metrics.stability < self.thresholds.stability:
            nudges.append("Stability wobbly: audit telemetry variance.")
        return nudges

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _resolve_commit() -> str:
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"


__all__ = [
    "AmplifyMetrics",
    "AmplifySnapshot",
    "AmplifyThresholds",
    "AmplifyWeights",
    "AmplifyState",
    "AmplifyGateError",
    "AmplificationEngine",
]

