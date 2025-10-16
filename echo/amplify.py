"""Amplification engine for EchoEvolver cycles."""
from __future__ import annotations

import json
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Mapping, MutableMapping, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from .evolver import EvolverState


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


DEFAULT_WEIGHT_PROFILE: Mapping[str, float] = {
    "resonance": 24.0,
    "freshness_half_life": 15.0,
    "novelty_delta": 20.0,
    "cohesion": 14.0,
    "coverage": 15.0,
    "volatility": 10.0,
}

DEFAULT_THRESHOLDS: Mapping[str, float] = {
    "resonance": 0.55,
    "freshness_half_life": 0.5,
    "novelty_delta": 0.4,
    "cohesion": 0.6,
    "coverage": 0.6,
    "stability": 0.55,
}

NUDGE_MESSAGES: Mapping[str, str] = {
    "resonance": "Low resonance: rebalance emotional drive with joy rituals.",
    "freshness_half_life": "Freshness decay detected: replay synthesis loop X to refresh signals.",
    "novelty_delta": "Low novelty: mutate rule space with glyph perturbation X.",
    "cohesion": "Cohesion drop: run refactor pass Y across mythocode.",
    "coverage": "Coverage gap: extend entity alignment sweep Z.",
    "stability": "Stability wobble: stabilise system metrics with telemetry calibration.",
}


@dataclass(frozen=True)
class AmplifySnapshot:
    cycle: int
    metrics: Mapping[str, float]
    index: float
    timestamp: str
    commit_sha: str

    def to_dict(self) -> Dict[str, object]:
        metrics = {key: round(value, 4) for key, value in self.metrics.items()}
        return {
            "cycle": self.cycle,
            "metrics": metrics,
            "index": round(self.index, 4),
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class AmplificationEngine:
    def __init__(
        self,
        *,
        repo_root: Path | str | None = None,
        weight_profile: Optional[Mapping[str, float]] = None,
        thresholds: Optional[Mapping[str, float]] = None,
        time_source: Optional[Callable[[], float]] = None,
        commit_resolver: Optional[Callable[[], str]] = None,
    ) -> None:
        self.repo_root = Path(repo_root or Path.cwd())
        self.weight_profile: Dict[str, float] = dict(DEFAULT_WEIGHT_PROFILE)
        if weight_profile:
            self.weight_profile.update(weight_profile)
        self.thresholds: Dict[str, float] = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)
        self.time_source = time_source or self._default_time_source
        self.commit_resolver = commit_resolver or self._default_commit_resolver
        self.log_path = self.repo_root / "state" / "amplify_log.jsonl"
        self.manifest_path = self.repo_root / "echo_manifest.json"
        self._history: List[AmplifySnapshot] = []
        self._load_history()

    @staticmethod
    def _default_time_source() -> float:
        return datetime.now(timezone.utc).timestamp()

    @staticmethod
    def _default_commit_resolver() -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            sha = result.stdout.strip()
            return sha or "UNKNOWN"
        except (OSError, subprocess.CalledProcessError):
            return "UNKNOWN"

    @property
    def history(self) -> Sequence[AmplifySnapshot]:
        return tuple(self._history)

    def latest(self) -> Optional[AmplifySnapshot]:
        return self._history[-1] if self._history else None

    def _load_history(self) -> None:
        if not self.log_path.exists():
            return
        try:
            with self.log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    snapshot = AmplifySnapshot(
                        cycle=int(payload["cycle"]),
                        metrics=payload["metrics"],
                        index=float(payload["index"]),
                        timestamp=str(payload["timestamp"]),
                        commit_sha=str(payload["commit_sha"]),
                    )
                    self._history.append(snapshot)
        except (json.JSONDecodeError, OSError, KeyError, ValueError):
            # Corrupted log entries are ignored to keep pipeline resilient.
            self._history.clear()

    def _resolve_timestamp(self) -> str:
        value = self.time_source()
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    def _cycle_duration(self, state: EvolverState, *, cycle_start: Optional[float]) -> float:
        if cycle_start is None:
            return 0.0
        end = self.time_source()
        self._last_cycle_time = end
        return max(0.0, end - cycle_start)

    def _cycle_signature(self, state: EvolverState) -> Sequence[str]:
        return tuple(state.mythocode)

    def compute_metrics(
        self,
        state: "EvolverState",
        *,
        cycle_start: Optional[float],
        total_steps: int,
    ) -> MutableMapping[str, float]:
        duration = self._cycle_duration(state, cycle_start=cycle_start)
        joy = state.emotional_drive.joy
        curiosity = state.emotional_drive.curiosity
        rage = state.emotional_drive.rage
        resonance = _clamp((joy + curiosity + (1.0 - _clamp(rage))) / 3.0)

        half_life_seconds = 240.0
        freshness = _clamp(0.5 ** (duration / half_life_seconds))

        signature = set(self._cycle_signature(state))
        previous_signature = set(state.network_cache.get("amplify_last_signature", ()))
        if not signature:
            novelty = 0.0
        elif not previous_signature:
            novelty = 1.0
        else:
            union = signature | previous_signature
            if not union:
                novelty = 0.0
            else:
                novelty = 1.0 - (len(signature & previous_signature) / len(union))
        novelty = _clamp(novelty)

        completed = len(state.network_cache.get("completed_steps", set()))
        total = max(1, total_steps)
        cohesion = _clamp(completed / total)

        active_entities = sum(
            1
            for status in state.entities.values()
            if str(status).upper() not in {"INACTIVE", "DORMANT", "FAULT"}
        )
        coverage = _clamp(active_entities / max(1, len(state.entities)))

        metrics = state.system_metrics
        cpu_score = 1.0 - _clamp(metrics.cpu_usage / 100.0)
        orbital_score = _clamp(metrics.orbital_hops / 10.0)
        node_score = _clamp(metrics.network_nodes / 25.0)
        stability = _clamp((cpu_score + orbital_score + node_score) / 3.0)
        volatility = _clamp(1.0 - stability)

        return {
            "resonance": resonance,
            "freshness_half_life": freshness,
            "novelty_delta": novelty,
            "cohesion": cohesion,
            "coverage": coverage,
            "stability": stability,
            "volatility": volatility,
        }

    def compute_index(self, metrics: Mapping[str, float]) -> float:
        score = (
            self.weight_profile["resonance"] * metrics["resonance"]
            + self.weight_profile["freshness_half_life"] * metrics["freshness_half_life"]
            + self.weight_profile["novelty_delta"] * metrics["novelty_delta"]
            + self.weight_profile["cohesion"] * metrics["cohesion"]
            + self.weight_profile["coverage"] * metrics["coverage"]
            - self.weight_profile["volatility"] * metrics["volatility"]
        )
        return _clamp(score, 0.0, 100.0)

    def capture(
        self,
        state: "EvolverState",
        *,
        cycle_start: Optional[float],
        total_steps: int,
    ) -> AmplifySnapshot:
        metrics = self.compute_metrics(state, cycle_start=cycle_start, total_steps=total_steps)
        index = self.compute_index(metrics)
        timestamp = self._resolve_timestamp()
        commit_sha = self.commit_resolver()
        snapshot = AmplifySnapshot(
            cycle=state.cycle,
            metrics=metrics,
            index=round(index, 4),
            timestamp=timestamp,
            commit_sha=commit_sha,
        )
        state.network_cache["amplify_last_signature"] = tuple(self._cycle_signature(state))
        return snapshot

    def append_snapshot(self, snapshot: AmplifySnapshot) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(snapshot.to_json())
            handle.write("\n")
        self._history.append(snapshot)

    def rolling_average(self, window: int = 3) -> Optional[float]:
        if not self._history:
            return None
        values = [item.index for item in self._history[-window:]]
        return statistics.fmean(values)

    def generate_nudges(self, metrics: Mapping[str, float]) -> List[str]:
        nudges: List[str] = []
        for key, threshold in self.thresholds.items():
            value = metrics.get(key)
            if value is None:
                continue
            if value < threshold:
                nudges.append(NUDGE_MESSAGES.get(key, f"Metric {key} below threshold"))
        return nudges

    def update_manifest(self, snapshot: AmplifySnapshot, *, gate: Optional[float] = None) -> Optional[Dict[str, object]]:
        if not self.manifest_path.exists():
            return None
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
        amplification = manifest.get("amplification", {})
        amplification.update(
            {
                "latest": snapshot.to_dict(),
                "rolling_avg": round(self.rolling_average() or snapshot.index, 4),
                "gate": gate,
            }
        )
        manifest["amplification"] = amplification
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return amplification

    def ensure_snapshot(
        self,
        state: "EvolverState",
        *,
        cycle_start: Optional[float],
        total_steps: int,
        persist: bool = True,
    ) -> AmplifySnapshot:
        snapshot = self.capture(state, cycle_start=cycle_start, total_steps=total_steps)
        if persist:
            self.append_snapshot(snapshot)
        return snapshot


__all__ = ["AmplifySnapshot", "AmplificationEngine"]
