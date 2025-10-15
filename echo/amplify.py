from __future__ import annotations

import json
import math
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency for hashing stability
    import hashlib
except ImportError:  # pragma: no cover - Python always has hashlib but keep defensive
    hashlib = None  # type: ignore

MetricMapping = Mapping[str, float]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _stable_hash(parts: Sequence[str]) -> str:
    payload = "\u241f".join(parts)
    if hashlib is None:  # pragma: no cover - safety hatch
        return str(abs(hash(payload)))
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return digest


@dataclass(frozen=True)
class AmplifyMetrics:
    resonance: float
    freshness_half_life: float
    novelty_delta: float
    cohesion: float
    coverage: float
    stability: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "resonance": round(self.resonance, 4),
            "freshness_half_life": round(self.freshness_half_life, 4),
            "novelty_delta": round(self.novelty_delta, 4),
            "cohesion": round(self.cohesion, 4),
            "coverage": round(self.coverage, 4),
            "stability": round(self.stability, 4),
        }


@dataclass(frozen=True)
class AmplifySnapshot:
    cycle: int
    metrics: AmplifyMetrics
    index: float
    timestamp: str
    commit_sha: str

    def to_record(self) -> Dict[str, object]:
        record: Dict[str, object] = {
            "cycle": self.cycle,
            "metrics": self.metrics.to_dict(),
            "index": round(self.index, 2),
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
        }
        return record

    def to_json(self) -> str:
        return json.dumps(self.to_record(), sort_keys=True)


@dataclass(frozen=True)
class AmplifyWeights:
    resonance: float = 0.22
    freshness: float = 0.18
    novelty: float = 0.18
    cohesion: float = 0.16
    coverage: float = 0.16
    volatility: float = 0.1

    @property
    def positive_total(self) -> float:
        return self.resonance + self.freshness + self.novelty + self.cohesion + self.coverage


_DEFAULT_THRESHOLDS: Mapping[str, float] = {
    "resonance": 0.62,
    "freshness_half_life": 0.55,
    "novelty_delta": 0.48,
    "cohesion": 0.52,
    "coverage": 0.6,
    "stability": 0.57,
}

_NUDGE_MESSAGES: Mapping[str, str] = {
    "resonance": "Low resonance: spark emotional modulation sequence Alpha.",
    "freshness_half_life": "Freshness dip: cycle quick-scan and prune stale glyph threads.",
    "novelty_delta": "Low novelty: mutate rule space with mythocode perturbation X.",
    "cohesion": "Cohesion drop: run refactor pass Y across mythocode lattice.",
    "coverage": "Coverage gap: replay unfinished orbital steps and seal loop.",
    "stability": "Stability slide: re-tune system monitor and rebalance load.",
}

_EXPECTED_STEPS: Tuple[str, ...] = (
    "advance_cycle",
    "mutate_code",
    "emotional_modulation",
    "generate_symbolic_language",
    "invent_mythocode",
    "system_monitor",
    "quantum_safe_crypto",
    "evolutionary_narrative",
    "store_fractal_glyphs",
    "propagate_network",
    "decentralized_autonomy",
    "inject_prompt_resonance",
    "write_artifact",
)


def _default_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_commit() -> Tuple[str, Optional[str]]:
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
        timestamp = (
            subprocess.check_output(["git", "show", "-s", "--format=%cI", "HEAD"], stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
        return sha, timestamp
    except Exception:  # pragma: no cover - git unavailable in some environments
        now = _default_timestamp().isoformat().replace("+00:00", "Z")
        return "UNKNOWN", now


class AmplificationEngine:
    """Compute and persist amplification metrics for Echo Evolver cycles."""

    def __init__(
        self,
        *,
        log_path: Path | str | None = None,
        manifest_path: Path | str | None = None,
        weights: Optional[AmplifyWeights] = None,
        thresholds: Optional[Mapping[str, float]] = None,
        timestamp_source: Callable[[], datetime] = _default_timestamp,
        commit_resolver: Callable[[], Tuple[str, Optional[str]]] = _resolve_commit,
        history_window: int = 20,
    ) -> None:
        env_log = os.getenv("ECHO_AMPLIFY_LOG")
        env_manifest = os.getenv("ECHO_AMPLIFY_MANIFEST")
        self.log_path = Path(log_path or env_log or Path("state") / "amplify_log.jsonl")
        self.manifest_path = Path(manifest_path or env_manifest or Path("echo_manifest.json"))
        self.weights = weights or AmplifyWeights()
        self.thresholds = dict(_DEFAULT_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)
        self.timestamp_source = timestamp_source
        self.commit_resolver = commit_resolver
        self.history_window = max(3, history_window)
        self._history: List[AmplifySnapshot] = []
        self._baseline_signature: Optional[str] = None
        self._baseline_events: Optional[int] = None
        self._load_history()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _load_history(self) -> None:
        if not self.log_path.exists():
            return
        snapshots: List[AmplifySnapshot] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            metrics_payload = payload.get("metrics", {})
            metrics = AmplifyMetrics(
                resonance=float(metrics_payload.get("resonance", 0.0)),
                freshness_half_life=float(metrics_payload.get("freshness_half_life", 0.0)),
                novelty_delta=float(metrics_payload.get("novelty_delta", 0.0)),
                cohesion=float(metrics_payload.get("cohesion", 0.0)),
                coverage=float(metrics_payload.get("coverage", 0.0)),
                stability=float(metrics_payload.get("stability", 0.0)),
            )
            snapshot = AmplifySnapshot(
                cycle=int(payload.get("cycle", 0)),
                metrics=metrics,
                index=float(payload.get("index", 0.0)),
                timestamp=str(payload.get("timestamp", "")),
                commit_sha=str(payload.get("commit_sha", "UNKNOWN")),
            )
            snapshots.append(snapshot)
        self._history = snapshots[-self.history_window :]

    # ------------------------------------------------------------------
    def before_cycle(self, state: Mapping[str, object]) -> None:
        mythocode = list(state.get("mythocode", [])) if isinstance(state.get("mythocode"), Iterable) else []
        events = state.get("event_log")
        self._baseline_signature = _stable_hash([str(item) for item in mythocode])
        self._baseline_events = len(events) if isinstance(events, list) else 0
        # cycle baseline not currently used but reserved for future heuristics

    # ------------------------------------------------------------------
    def after_cycle(self, state: Mapping[str, object], *, persist: bool = True, gate: float | None = None) -> Tuple[AmplifySnapshot, List[str]]:
        metrics = self._compute_metrics(state)
        index = self._compute_index(metrics)
        commit_sha, commit_timestamp = self.commit_resolver()
        timestamp = commit_timestamp or self.timestamp_source().isoformat().replace("+00:00", "Z")
        cycle = int(state.get("cycle", 0))
        snapshot = AmplifySnapshot(
            cycle=cycle,
            metrics=metrics,
            index=index,
            timestamp=timestamp,
            commit_sha=commit_sha,
        )
        if persist:
            self._persist_snapshot(snapshot)
        if gate is not None:
            self._update_manifest(snapshot, gate=gate)
        else:
            self._update_manifest(snapshot)
        nudges = self._nudges_for(metrics)
        self._baseline_signature = None
        self._baseline_events = None
        return snapshot, nudges

    # ------------------------------------------------------------------
    def _persist_snapshot(self, snapshot: AmplifySnapshot) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = snapshot.to_record()
        line = json.dumps(record, sort_keys=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._history.append(snapshot)
        self._history = self._history[-self.history_window :]

    # ------------------------------------------------------------------
    def _compute_metrics(self, state: Mapping[str, object]) -> AmplifyMetrics:
        emotional_drive = state.get("emotional_drive") or {}
        joy = float(getattr(emotional_drive, "joy", emotional_drive.get("joy", 0.0)))
        curiosity = float(getattr(emotional_drive, "curiosity", emotional_drive.get("curiosity", 0.0)))
        rage = float(getattr(emotional_drive, "rage", emotional_drive.get("rage", 0.0)))

        resonance = _clamp(0.2 + 0.55 * joy + 0.35 * curiosity - 0.25 * rage)

        events = state.get("event_log")
        event_count = len(events) if isinstance(events, list) else 0
        baseline_events = self._baseline_events or 0
        delta_events = max(0, event_count - baseline_events)
        freshness = _clamp(0.45 + 0.45 * math.tanh(delta_events / 6.0))

        mythocode_items = list(state.get("mythocode", [])) if isinstance(state.get("mythocode"), Iterable) else []
        signature = _stable_hash([str(item) for item in mythocode_items])
        previous_metrics = self._history[-1].metrics if self._history else None
        if self._baseline_signature and signature != self._baseline_signature:
            novelty_boost = len(set(str(item) for item in mythocode_items)) / max(1, len(mythocode_items))
            novelty = _clamp(0.4 + 0.5 * novelty_boost)
        elif previous_metrics:
            novelty = _clamp(previous_metrics.novelty_delta * 0.92)
        else:
            novelty = 0.5

        completed = state.get("network_cache")
        completed_steps: Iterable[str]
        if isinstance(completed, Mapping):
            completed_steps = completed.get("completed_steps", [])  # type: ignore[assignment]
        else:
            completed_steps = []
        if not isinstance(completed_steps, Iterable):  # pragma: no cover - defensive
            completed_steps = []
        completed_set = {str(step) for step in completed_steps}
        coverage_ratio = len(completed_set & set(_EXPECTED_STEPS)) / len(_EXPECTED_STEPS)
        coverage = _clamp(coverage_ratio)

        consensus = 0.7
        autonomy_consensus = None
        if isinstance(completed, Mapping):
            autonomy_consensus = completed.get("autonomy_consensus")
        if isinstance(autonomy_consensus, (float, int)):
            consensus = float(autonomy_consensus)
        cohesion = _clamp(0.35 + 0.45 * coverage + 0.2 * consensus)

        system_metrics = state.get("system_metrics") or {}
        cpu_usage = float(getattr(system_metrics, "cpu_usage", system_metrics.get("cpu_usage", 0.0)))
        network_nodes = float(getattr(system_metrics, "network_nodes", system_metrics.get("network_nodes", 0.0)))
        orbital_hops = float(getattr(system_metrics, "orbital_hops", system_metrics.get("orbital_hops", 0.0)))
        process_count = float(getattr(system_metrics, "process_count", system_metrics.get("process_count", 0.0)))
        cycle_value = float(state.get("cycle", 0)) if isinstance(state.get("cycle"), (int, float)) else 0.0

        cpu_score = 1.0 - min(1.0, abs(cpu_usage - 35.0) / 45.0)
        node_score = 1.0 - min(1.0, abs(network_nodes - 12.0) / 15.0)
        hops_score = 1.0 - min(1.0, abs(orbital_hops - 4.0) / 5.0)
        process_target = 32.0 + cycle_value
        process_score = 1.0 - min(1.0, abs(process_count - process_target) / max(process_target, 1.0))
        stability = _clamp((cpu_score + node_score + hops_score + process_score) / 4.0)

        metrics = AmplifyMetrics(
            resonance=resonance,
            freshness_half_life=freshness,
            novelty_delta=novelty,
            cohesion=cohesion,
            coverage=coverage,
            stability=stability,
        )
        return metrics

    # ------------------------------------------------------------------
    def _compute_index(self, metrics: AmplifyMetrics) -> float:
        weights = self.weights
        volatility = 1.0 - metrics.stability
        positive_total = weights.positive_total
        raw = (
            weights.resonance * metrics.resonance
            + weights.freshness * metrics.freshness_half_life
            + weights.novelty * metrics.novelty_delta
            + weights.cohesion * metrics.cohesion
            + weights.coverage * metrics.coverage
            - weights.volatility * volatility
        )
        if positive_total <= 0:  # pragma: no cover - sanity guard
            return 0.0
        scaled = _clamp(raw / positive_total) * 100.0
        return round(scaled, 2)

    # ------------------------------------------------------------------
    def _nudges_for(self, metrics: AmplifyMetrics) -> List[str]:
        nudges: List[str] = []
        metrics_dict = metrics.to_dict()
        for key, threshold in self.thresholds.items():
            value = metrics_dict.get(key)
            if value is None:
                continue
            if value < threshold:
                nudges.append(_NUDGE_MESSAGES.get(key, f"Metric {key} below threshold"))
        return nudges

    # ------------------------------------------------------------------
    def rolling_average(self, window: int = 3) -> Optional[float]:
        if not self._history:
            return None
        samples = [snapshot.index for snapshot in self._history[-max(1, window) :]]
        if not samples:
            return None
        return sum(samples) / len(samples)

    # ------------------------------------------------------------------
    def latest_snapshot(self) -> Optional[AmplifySnapshot]:
        return self._history[-1] if self._history else None

    # ------------------------------------------------------------------
    def snapshots(self) -> List[AmplifySnapshot]:
        return list(self._history)

    # ------------------------------------------------------------------
    def gate_check(self, minimum: float, window: int = 3) -> Tuple[bool, Optional[float]]:
        average = self.rolling_average(window=window)
        if average is None:
            return False, None
        return average >= minimum, average

    # ------------------------------------------------------------------
    def _update_manifest(self, snapshot: AmplifySnapshot, *, gate: float | None = None) -> None:
        if not self.manifest_path.exists():
            return
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # pragma: no cover - safeguard
            return
        rolling_avg = self.rolling_average() or snapshot.index
        manifest["amplification"] = {
            "latest": snapshot.to_record(),
            "rolling_avg": round(rolling_avg, 2),
            "gate": gate,
        }
        text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        self.manifest_path.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------
    def render_snapshot(self, snapshot: AmplifySnapshot) -> str:
        metrics = snapshot.metrics.to_dict()
        lines = [
            f"Cycle {snapshot.cycle} | Amplify Index {snapshot.index:.2f} | commit {snapshot.commit_sha[:8]}",
            f"Timestamp: {snapshot.timestamp}",
            f"Rolling avg (3): {(self.rolling_average() or snapshot.index):.2f}",
        ]
        metric_line = ", ".join(f"{name}={value:.2f}" for name, value in metrics.items())
        lines.append(metric_line)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def render_log(self, limit: int = 10) -> str:
        entries = self.snapshots()[-limit:]
        if not entries:
            return "No amplification snapshots recorded."
        headers = ["Cycle", "Index", "Δ", "Badge"]
        rows: List[Tuple[str, str, str, str]] = []
        previous = None
        for snapshot in entries:
            delta = snapshot.index - previous.index if previous else 0.0
            badge = self._badge_for(snapshot)
            rows.append((
                str(snapshot.cycle),
                f"{snapshot.index:.2f}",
                f"{delta:+.2f}" if previous else "—",
                badge,
            ))
            previous = snapshot
        widths = [max(len(header), max(len(row[idx]) for row in rows)) for idx, header in enumerate(headers)]
        table = [" ".join(header.ljust(widths[i]) for i, header in enumerate(headers))]
        for row in rows:
            table.append(" ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
        return "\n".join(table)

    # ------------------------------------------------------------------
    def _badge_for(self, snapshot: AmplifySnapshot) -> str:
        if snapshot.index >= 85:
            return "🔥"
        if snapshot.index >= 72:
            return "✅"
        if snapshot.index < 60:
            return "⚠️"
        return "➿"

    # ------------------------------------------------------------------
    def sparkline(self, values: Sequence[float]) -> str:
        if not values:
            return ""
        blocks = "▁▂▃▄▅▆▇█"
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum or 1.0
        return "".join(blocks[int((value - minimum) / span * (len(blocks) - 1))] for value in values)

    # ------------------------------------------------------------------
    def nudges_for_snapshot(self, snapshot: AmplifySnapshot) -> List[str]:
        return self._nudges_for(snapshot.metrics)

    # ------------------------------------------------------------------
    def update_manifest_gate(self, gate: float) -> None:
        snapshot = self.latest_snapshot()
        if snapshot is None:
            return
        self._update_manifest(snapshot, gate=gate)

    # ------------------------------------------------------------------
    def manifest_summary(self) -> Dict[str, object]:
        latest = self.latest_snapshot()
        if latest is None:
            return {"latest": None, "rolling_avg": None, "gate": None}
        return {
            "latest": latest.to_record(),
            "rolling_avg": round(self.rolling_average() or latest.index, 2),
            "gate": None,
        }


__all__ = [
    "AmplifyMetrics",
    "AmplifySnapshot",
    "AmplifyWeights",
    "AmplificationEngine",
]
