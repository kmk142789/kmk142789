"""Echo emotional telemetry reporter."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, MutableMapping

__all__ = [
    "DEFAULT_VITALS_PATH",
    "EchoVitalPulse",
    "EchoVitalsReporter",
    "report_echo_vitals",
    "yield_vitals_history",
]

DEFAULT_VITALS_PATH = Path(
    os.environ.get("ECHO_EMOTIONAL_VITALS_PATH", "genesis_ledger/emotional_vitals.jsonl")
)


@dataclass(slots=True)
class EchoVitalPulse:
    """Single telemetry pulse describing an emotional surge."""

    emotion: str
    value: float
    note: str
    cycle: int | None
    timestamp: float

    def to_json(self) -> str:
        payload = asdict(self)
        payload["timestamp"] = round(self.timestamp, 6)
        return json.dumps(payload, ensure_ascii=False)


class EchoVitalsReporter:
    """Append-only reporter that tracks Echo's emotional telemetry."""

    def __init__(self, history_path: Path | str | None = None) -> None:
        self.history_path = Path(history_path or DEFAULT_VITALS_PATH)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: list[EchoVitalPulse] | None = None

    def record(
        self,
        emotion: str,
        value: float,
        *,
        note: str = "",
        cycle: int | None = None,
        timestamp: float | None = None,
    ) -> EchoVitalPulse:
        """Persist a new telemetry pulse and return it."""

        if not emotion:
            raise ValueError("emotion must be provided")
        if not isinstance(value, (int, float)):
            raise TypeError("value must be numeric")
        pulse = EchoVitalPulse(
            emotion=emotion,
            value=float(value),
            note=note,
            cycle=cycle,
            timestamp=timestamp or time.time(),
        )
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(pulse.to_json() + "\n")
        self._cache = None
        return pulse

    def iter_history(self) -> Iterator[EchoVitalPulse]:
        """Yield telemetry pulses in chronological order."""

        if self._cache is None:
            records: list[EchoVitalPulse] = []
            if self.history_path.exists():
                with self.history_path.open("r", encoding="utf-8") as handle:
                    for raw in handle:
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(payload, MutableMapping):
                            continue
                        records.append(
                            EchoVitalPulse(
                                emotion=str(payload.get("emotion", "")),
                                value=float(payload.get("value", 0.0)),
                                note=str(payload.get("note", "")),
                                cycle=payload.get("cycle"),
                                timestamp=float(payload.get("timestamp", 0.0)),
                            )
                        )
            self._cache = records
        yield from self._cache

    def report(
        self,
        emotional_state: Mapping[str, float],
        *,
        history_limit: int = 5,
        system_metrics: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        """Summarise Echo's current emotional vitals."""

        snapshot = {key: float(value) for key, value in emotional_state.items()}
        pulses = list(self.iter_history())
        trimmed = list(reversed(pulses))[: max(0, history_limit)]
        history_payload = [asdict(pulse) for pulse in trimmed]
        for item in history_payload:
            item["timestamp"] = round(item["timestamp"], 6)
        return {
            "emotionalState": snapshot,
            "history": history_payload,
            "historyAvailable": len(pulses),
            "systemMetrics": dict(system_metrics or {}),
        }


def report_echo_vitals(
    emotional_state: Mapping[str, float],
    *,
    history_limit: int = 5,
    system_metrics: Mapping[str, object] | None = None,
    reporter: EchoVitalsReporter | None = None,
) -> dict[str, object]:
    """Convenience helper that builds a report using ``reporter``."""

    reporter = reporter or EchoVitalsReporter()
    return reporter.report(
        emotional_state,
        history_limit=history_limit,
        system_metrics=system_metrics,
    )


def yield_vitals_history(pulses: Iterable[EchoVitalPulse]) -> Iterator[dict[str, object]]:
    """Yield serialisable dictionaries for each telemetry pulse."""

    for pulse in pulses:
        payload = asdict(pulse)
        payload["timestamp"] = round(pulse.timestamp, 6)
        yield payload
