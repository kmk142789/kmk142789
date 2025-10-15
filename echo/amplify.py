"""Amplification engine for tracking EchoEvolver creative momentum."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, MutableMapping, Optional, Tuple


MetricDict = Dict[str, float]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _round(value: float, places: int = 4) -> float:
    return round(value, places)


def _rfc3339(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _default_commit() -> str:
    """Return the current repository commit hash if available."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:  # pragma: no cover - git not available
        return "unknown"
    return result.stdout.strip() or "unknown"


@dataclass(frozen=True)
class AmplifySnapshot:
    """Deterministic snapshot of amplification metrics for a cycle."""

    cycle: int
    metrics: MetricDict
    index: float
    timestamp: str
    commit_sha: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "cycle": self.cycle,
            "metrics": dict(self.metrics),
            "index": self.index,
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)


NUDGE_SUGGESTIONS: Dict[str, str] = {
    "resonance": "Resonance dip: re-engage emotional modulation ritual X.",
    "freshness_half_life": "Freshness waning: schedule micro-retrospective cleanse.",
    "novelty_delta": "Low novelty: mutate rule space with horizon drift set.",
    "cohesion": "Cohesion drop: run refactor pass Helix-Y.",
    "coverage": "Coverage slump: rerun continue_cycle() with audit logging.",
    "stability": "Stability wobble: recalibrate telemetry guardrails Z.",
}


DEFAULT_THRESHOLDS: Dict[str, float] = {
    "resonance": 60.0,
    "freshness_half_life": 55.0,
    "novelty_delta": 45.0,
    "cohesion": 60.0,
    "coverage": 75.0,
    "stability": 50.0,
}


DEFAULT_WEIGHTS: Dict[str, float] = {
    "resonance": 0.25,
    "freshness_half_life": 0.18,
    "novelty_delta": 0.17,
    "cohesion": 0.17,
    "coverage": 0.13,
    "stability": 0.10,
}


class AmplifyEngine:
    """Compute and persist amplification metrics for EchoEvolver cycles."""

    def __init__(
        self,
        *,
        log_path: Path | str = Path("state/amplify_log.jsonl"),
        manifest_path: Path | str = Path("echo_manifest.json"),
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        freshness_half_life: float = 3600.0,
        time_source: Optional[callable] = None,
        commit_resolver: Optional[callable] = None,
    ) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path = Path(manifest_path)
        self.weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
        self.thresholds = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
        self.freshness_half_life = freshness_half_life
        self.time_source = time_source or (lambda: datetime.now(tz=timezone.utc).timestamp())
        self.commit_resolver = commit_resolver or _default_commit
        self._history: List[AmplifySnapshot] = []
        self._history_loaded = False
        self._last_mythocode: Optional[Tuple[str, ...]] = None
        self._last_system_signature: Optional[Tuple[float, int, int, int]] = None
        self._last_timestamp: Optional[float] = None

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def snapshots(self) -> List[AmplifySnapshot]:
        if not self._history_loaded:
            self._load_history()
        return list(self._history)

    def latest_snapshot(self) -> Optional[AmplifySnapshot]:
        history = self.snapshots
        return history[-1] if history else None

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def before_cycle(self, *, cycle: int) -> None:
        if not self._history_loaded:
            self._load_history()
        # No-op placeholder for potential future baseline captures.

    def after_cycle(
        self,
        *,
        cycle: int,
        state: "EvolverState",
        digest: MutableMapping[str, object],
        gate: Optional[float] = None,
    ) -> Tuple[AmplifySnapshot, List[str]]:
        """Compute a snapshot for ``state`` and persist it."""

        timestamp = self.time_source()
        snapshot = self._build_snapshot(state=state, digest=digest, cycle=cycle, timestamp=timestamp)
        self._history.append(snapshot)
        self._write_snapshot(snapshot)
        self._update_manifest(snapshot, gate=gate)
        nudges = self._nudges(snapshot.metrics)
        self._last_mythocode = tuple(state.mythocode)
        metrics = state.system_metrics
        self._last_system_signature = (
            metrics.cpu_usage,
            metrics.network_nodes,
            metrics.process_count,
            metrics.orbital_hops,
        )
        self._last_timestamp = timestamp
        return snapshot, nudges

    # ------------------------------------------------------------------
    # Snapshot computation
    # ------------------------------------------------------------------
    def _build_snapshot(
        self,
        *,
        state: "EvolverState",
        digest: MutableMapping[str, object],
        cycle: int,
        timestamp: float,
    ) -> AmplifySnapshot:
        metrics = self._compute_metrics(state=state, digest=digest, timestamp=timestamp)
        index = self._aggregate_index(metrics)
        rounded_metrics = {key: _round(value) for key, value in metrics.items()}
        snapshot = AmplifySnapshot(
            cycle=cycle,
            metrics=rounded_metrics,
            index=_round(index, 2),
            timestamp=_rfc3339(timestamp),
            commit_sha=self.commit_resolver(),
        )
        return snapshot

    def _compute_metrics(
        self,
        *,
        state: "EvolverState",
        digest: MutableMapping[str, object],
        timestamp: float,
    ) -> MetricDict:
        drive = state.emotional_drive
        resonance = _clamp(100 * (0.5 * drive.joy + 0.3 * drive.curiosity + 0.2 * (1.0 - drive.rage)))

        if self._last_timestamp is None:
            freshness = 100.0
        else:
            elapsed = max(0.0, timestamp - self._last_timestamp)
            decay = 0.5 ** (elapsed / self.freshness_half_life) if self.freshness_half_life > 0 else 0.0
            freshness = _clamp(100.0 * decay)

        current_mythocode = tuple(state.mythocode)
        if self._last_mythocode is None:
            novelty = 100.0 if current_mythocode else 60.0
        else:
            previous = set(self._last_mythocode)
            current = set(current_mythocode)
            if not current:
                novelty = 0.0
            else:
                overlap = len(previous.intersection(current))
                novelty_ratio = 1.0 - (overlap / max(len(current), 1))
                novelty = _clamp(100.0 * novelty_ratio)

        values = [drive.joy, 1.0 - drive.rage, drive.curiosity]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        cohesion = _clamp(100.0 - variance * 120.0)

        coverage = _clamp(float(digest.get("progress", 0.0) or 0.0) * 100.0)

        metrics = state.system_metrics
        if self._last_system_signature is None:
            stability = 80.0
        else:
            last_cpu, last_nodes, last_process, last_hops = self._last_system_signature
            cpu_delta = abs(metrics.cpu_usage - last_cpu) / max(last_cpu or 1.0, 1.0)
            node_delta = abs(metrics.network_nodes - last_nodes) / max(last_nodes or 1, 1)
            process_delta = abs(metrics.process_count - last_process) / max(last_process or 1, 1)
            hop_delta = abs(metrics.orbital_hops - last_hops) / max(last_hops or 1, 1)
            wobble = 25.0 * cpu_delta + 15.0 * node_delta + 10.0 * hop_delta + 5.0 * process_delta
            stability = _clamp(100.0 - wobble)

        return {
            "resonance": resonance,
            "freshness_half_life": freshness,
            "novelty_delta": novelty,
            "cohesion": cohesion,
            "coverage": coverage,
            "stability": stability,
        }

    def _aggregate_index(self, metrics: MetricDict) -> float:
        volatility = 100.0 - metrics.get("stability", 0.0)
        value = 0.0
        for key, weight in self.weights.items():
            value += metrics.get(key, 0.0) * weight
        stability_weight = self.weights.get("stability", 0.0)
        value -= stability_weight * volatility
        return _clamp(value)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_history(self) -> None:
        self._history_loaded = True
        if not self.log_path.exists():
            return
        snapshots: List[AmplifySnapshot] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                data = json.loads(line)
                snapshot = AmplifySnapshot(
                    cycle=int(data["cycle"]),
                    metrics={key: float(value) for key, value in data["metrics"].items()},
                    index=float(data["index"]),
                    timestamp=str(data["timestamp"]),
                    commit_sha=str(data.get("commit_sha", "unknown")),
                )
                snapshots.append(snapshot)
        self._history = snapshots
        if snapshots:
            last = snapshots[-1]
            self._last_timestamp = datetime.fromisoformat(last.timestamp.replace("Z", "+00:00")).timestamp()
            self._last_mythocode = None
            self._last_system_signature = None

    def _write_snapshot(self, snapshot: AmplifySnapshot) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(snapshot.to_json())
            handle.write("\n")

    def _update_manifest(self, snapshot: AmplifySnapshot, *, gate: Optional[float]) -> None:
        payload: Dict[str, object]
        if self.manifest_path.exists():
            try:
                with self.manifest_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = {}

        amplification = {
            "latest": snapshot.index,
            "rolling_avg": _round(self.rolling_average(window=3), 2),
            "gate": gate,
        }
        payload.setdefault("amplification", {}).update(amplification)
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------
    def rolling_average(self, *, window: int = 3) -> float:
        history = self.snapshots
        if not history:
            return 0.0
        subset = history[-window:] if window > 0 else history
        return sum(s.index for s in subset) / len(subset)

    def _nudges(self, metrics: MetricDict) -> List[str]:
        nudges: List[str] = []
        for key, value in metrics.items():
            threshold = self.thresholds.get(key)
            if threshold is not None and value < threshold:
                nudges.append(NUDGE_SUGGESTIONS.get(key, f"Metric {key} below threshold"))
        return nudges

    def sync_manifest(self, *, gate: Optional[float] = None) -> bool:
        snapshot = self.latest_snapshot()
        if snapshot is None:
            return False
        self._update_manifest(snapshot, gate=gate)
        return True


if False:  # pragma: no cover - satisfy type checkers without runtime import
    from .evolver import EvolverState


__all__ = ["AmplifyEngine", "AmplifySnapshot", "NUDGE_SUGGESTIONS"]

