from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

from .config import AmplifyConfig

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent

try:  # pragma: no cover - optional dependency for tighter typing
    from typing import TypedDict
except ImportError:  # pragma: no cover
    TypedDict = dict  # type: ignore[misc,assignment]

if TypedDict is dict:  # pragma: no cover - fallback branch for older Python
    AmplifySummaryDict = Dict[str, object]
else:
    class AmplifySummaryDict(TypedDict, total=False):
        latest: Optional[Dict[str, object]]
        rolling_3: Optional[float]
        gate: Dict[str, object]


if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from .evolver import EvolverState


@dataclass(frozen=True)
class AmplificationMetrics:
    """Computed metrics feeding the Amplify Index."""

    resonance: float
    freshness_half_life: float
    novelty_delta: float
    cohesion: float
    coverage: float
    volatility: float
    index: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "resonance": self.resonance,
            "freshness_half_life": self.freshness_half_life,
            "novelty_delta": self.novelty_delta,
            "cohesion": self.cohesion,
            "coverage": self.coverage,
            "volatility": self.volatility,
            "index": self.index,
        }


@dataclass(frozen=True)
class AmplifyRecord:
    """Single JSONL entry stored by the Amplify engine."""

    timestamp: float
    metrics: AmplificationMetrics
    cycle: Optional[int] = None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "timestamp": round(self.timestamp, 4),
            "metrics": self.metrics.to_dict(),
        }
        if self.cycle is not None:
            payload["cycle"] = self.cycle
        return payload


def _clamp(value: float, *, precision: int = 2) -> float:
    return round(max(0.0, min(100.0, value)), precision)


class AmplifyEngine:
    """Derives amplification metrics and persists them for historical tracking."""

    METRIC_NAMES: Tuple[str, ...] = (
        "resonance",
        "freshness_half_life",
        "novelty_delta",
        "cohesion",
        "coverage",
        "volatility",
    )

    def __init__(
        self,
        *,
        repo_root: Optional[Path] = None,
        config: Optional[AmplifyConfig] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.repo_root = Path(repo_root or DEFAULT_REPO_ROOT)
        self.config = config or AmplifyConfig()
        self.clock = clock or __import__("time").time

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def measure(self, state: Optional["EvolverState"] = None) -> AmplificationMetrics:
        """Compute the amplification metrics.

        When ``state`` is provided the calculation leverages the active
        :class:`~echo.evolver.EvolverState`.  Otherwise repository-wide
        indicators are sampled which keeps the command usable even outside of
        live evolver runs.
        """

        if state is not None:
            raw_metrics = self._metrics_from_state(state)
        else:
            raw_metrics = self._metrics_from_repository()

        weights = self.config.weights.normalised()
        index = 0.0
        for name in self.METRIC_NAMES:
            index += raw_metrics[name] * weights.get(name, 0.0)
        metrics = AmplificationMetrics(index=_clamp(index), **raw_metrics)
        return metrics

    def measure_and_record(self, state: Optional["EvolverState"] = None, *, cycle: Optional[int] = None) -> AmplifyRecord:
        metrics = self.measure(state)
        return self.record(metrics, cycle=cycle)

    def record(self, metrics: AmplificationMetrics, *, cycle: Optional[int] = None) -> AmplifyRecord:
        timestamp = self.clock()
        record = AmplifyRecord(timestamp=timestamp, metrics=metrics, cycle=cycle)
        log_path = self.repo_root / self.config.log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            json.dump(record.to_dict(), handle, sort_keys=True)
            handle.write("\n")
        return record

    def iter_records(self) -> Iterator[AmplifyRecord]:
        log_path = self.repo_root / self.config.log_path
        if not log_path.exists():
            return iter(())

        def _generate() -> Iterator[AmplifyRecord]:
            with log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    metrics = AmplificationMetrics(**payload["metrics"])
                    yield AmplifyRecord(
                        timestamp=float(payload["timestamp"]),
                        metrics=metrics,
                        cycle=payload.get("cycle"),
                    )

        return _generate()

    def latest(self) -> Optional[AmplifyRecord]:
        records = list(self.iter_records())
        return records[-1] if records else None

    def rolling_average(self, window: Optional[int] = None) -> Optional[float]:
        window = window or self.config.rolling_window
        if window <= 0:
            return None
        records = list(self.iter_records())
        if not records:
            return None
        slice_start = max(0, len(records) - window)
        values = [record.metrics.index for record in records[slice_start:]]
        return _clamp(sum(values) / len(values))

    def tail(self, count: int = 10) -> List[AmplifyRecord]:
        if count <= 0:
            return []
        records = list(self.iter_records())
        return records[-count:]

    def sparkline(self, count: int = 8) -> str:
        records = self.tail(count)
        values = [record.metrics.index for record in records]
        if not values:
            return ""
        low = min(values)
        high = max(values)
        if math.isclose(low, high):
            return "▇" * len(values)
        slots = "▁▂▃▄▅▆▇█"
        span = high - low
        return "".join(slots[int((value - low) / span * (len(slots) - 1))] for value in values)

    def ensure_gate(self, minimum: Optional[float] = None) -> Tuple[bool, Optional[float]]:
        minimum = self._resolve_gate_floor(minimum)
        latest = self.latest()
        if latest is None:
            return False, None
        index = latest.metrics.index
        return index >= minimum, index

    def summary(self) -> AmplifySummaryDict:
        latest = self.latest()
        gate_floor = self.config.gate_floor
        summary: AmplifySummaryDict = {
            "latest": latest.to_dict() if latest else None,
            "rolling_3": self.rolling_average(),
            "gate": {
                "floor": gate_floor,
                "current": latest.metrics.index if latest else None,
                "status": self._gate_status(latest, gate_floor),
            },
        }
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_gate_floor(self, minimum: Optional[float]) -> float:
        return float(self.config.gate_floor if minimum is None else minimum)

    def _gate_status(self, latest: Optional[AmplifyRecord], floor: float) -> str:
        if latest is None:
            return "unknown"
        return "pass" if latest.metrics.index >= floor else "fail"

    def _metrics_from_state(self, state: "EvolverState") -> Dict[str, float]:
        joy = getattr(state.emotional_drive, "joy", 0.0)
        curiosity = getattr(state.emotional_drive, "curiosity", 0.0)
        resonance = _clamp(((joy + curiosity) / 2.0) * 100.0)

        freshness = _clamp(100.0 - state.cycle * 3.5)

        mythocode = list(getattr(state, "mythocode", []))
        novelty = _clamp(45.0 + len(set(mythocode)) * 7.5)

        event_log = getattr(state, "event_log", [])
        cohesion = _clamp(55.0 + (len(event_log) / max(1, state.cycle)) * 4.5)

        entities = getattr(state, "entities", {})
        glyphs = getattr(state, "glyphs", "")
        coverage = _clamp(50.0 + len(entities) * 4.0 + len(glyphs) * 0.4)

        metrics = getattr(state, "system_metrics", None)
        if metrics is None:
            volatility = 50.0
        else:
            volatility = 40.0
            volatility += getattr(metrics, "network_nodes", 0) * 1.8
            volatility -= getattr(metrics, "orbital_hops", 0) * 1.2
            volatility += getattr(metrics, "cpu_usage", 0.0) * 0.35
        volatility = _clamp(volatility)

        return {
            "resonance": resonance,
            "freshness_half_life": freshness,
            "novelty_delta": novelty,
            "cohesion": cohesion,
            "coverage": coverage,
            "volatility": volatility,
        }

    def _metrics_from_repository(self) -> Dict[str, float]:
        history = self._load_pulse_history()
        timestamps = [entry["timestamp"] for entry in history if "timestamp" in entry]
        now = self.clock()

        resonance = _clamp(45.0 + min(50.0, len(history[-20:]) * 3.2))

        if timestamps:
            age_hours = (now - max(timestamps)) / 3600.0
            freshness = _clamp(100.0 - age_hours * 6.0)
        else:
            freshness = 65.0

        unique_messages = len({entry.get("message", "") for entry in history[-20:]})
        novelty = _clamp(40.0 + unique_messages * 4.5)

        docs_root = self.repo_root / "docs"
        doc_count = sum(1 for _ in docs_root.rglob("*.md")) if docs_root.exists() else 0
        cohesion = _clamp(50.0 + min(40.0, doc_count * 0.8))

        dataset_count = self._dataset_count()
        coverage = _clamp(45.0 + min(45.0, dataset_count * 3.5))

        volatility = self._volatility_from_history(timestamps)

        return {
            "resonance": resonance,
            "freshness_half_life": freshness,
            "novelty_delta": novelty,
            "cohesion": cohesion,
            "coverage": coverage,
            "volatility": volatility,
        }

    def _dataset_count(self) -> int:
        directories = (
            "datasets",
            "data",
            "docs/data",
            "federated_pulse",
            "genesis_ledger",
            "ledger",
            "manifest",
        )
        count = 0
        for directory in directories:
            base = self.repo_root / directory
            if not base.exists():
                continue
            for item in base.rglob("*"):
                if item.is_file():
                    count += 1
        return count

    def _load_pulse_history(self) -> List[Dict[str, object]]:
        path = self.repo_root / "pulse_history.json"
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def _volatility_from_history(self, timestamps: Sequence[float]) -> float:
        if len(timestamps) < 2:
            return 55.0
        intervals = [abs(b - a) for a, b in zip(timestamps, timestamps[1:])]
        if not intervals:
            return 55.0
        avg_interval = sum(intervals) / len(intervals)
        scaled = 60.0 - min(35.0, avg_interval / 120.0)
        return _clamp(scaled)


__all__ = [
    "AmplificationMetrics",
    "AmplifyEngine",
    "AmplifyRecord",
]
