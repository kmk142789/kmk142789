"""Transparent Reflection Layer primitives and emitters."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.telemetry.collector import TelemetryCollector
from src.telemetry.schema import TelemetryContext


@dataclass(frozen=True)
class ReflectionMetric:
    """Scalar value describing a reflection-oriented telemetry datapoint."""

    key: str
    value: float | int
    unit: str | None = None
    info: str | None = None

    def as_payload(self) -> Mapping[str, object]:
        payload: MutableMapping[str, object] = {"key": self.key, "value": self.value}
        if self.unit:
            payload["unit"] = self.unit
        if self.info:
            payload["info"] = self.info
        return payload


@dataclass(frozen=True)
class ReflectionTrace:
    """Structured note attached to a reflection snapshot."""

    event: str
    detail: Mapping[str, object] = field(default_factory=dict)
    level: str = "info"

    def as_payload(self) -> Mapping[str, object]:
        payload: MutableMapping[str, object] = {
            "event": self.event,
            "level": self.level,
        }
        if self.detail:
            payload["detail"] = dict(self.detail)
        return payload


@dataclass(frozen=True)
class ReflectionSnapshot:
    """Immutable container representing a reflection emission."""

    component: str
    metrics: Sequence[ReflectionMetric] = field(default_factory=tuple)
    traces: Sequence[ReflectionTrace] = field(default_factory=tuple)
    safeguards: Sequence[str] = field(default_factory=tuple)
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_payload(self) -> dict[str, object]:
        metrics_payload = [metric.as_payload() for metric in self.metrics if metric.key]
        traces_payload = [trace.as_payload() for trace in self.traces if trace.event]
        safeguards_payload = [item for item in self.safeguards if item]
        diagnostics_payload = {
            key: value
            for key, value in self.diagnostics.items()
            if value is not None and key
        }
        return {
            "component": self.component,
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat(),
            "metrics": metrics_payload,
            "traces": traces_payload,
            "safeguards": safeguards_payload,
            "diagnostics": diagnostics_payload,
        }


class TransparentReflectionLayer:
    """Coordinator emitting sanitized reflection snapshots with telemetry."""

    def __init__(
        self,
        *,
        component: str,
        collector: TelemetryCollector | None = None,
        context: TelemetryContext | None = None,
    ) -> None:
        self._component = component
        self._collector = collector
        self._context = context

    def emit(
        self,
        *,
        metrics: Iterable[ReflectionMetric | Mapping[str, object]] = (),
        traces: Iterable[ReflectionTrace | Mapping[str, object]] = (),
        safeguards: Iterable[str] = (),
        diagnostics: Mapping[str, object] | None = None,
        generated_at: datetime | None = None,
    ) -> dict[str, object]:
        """Produce a snapshot and optionally persist telemetry."""

        snapshot = ReflectionSnapshot(
            component=self._component,
            metrics=tuple(self._coerce_metric(item) for item in metrics),
            traces=tuple(self._coerce_trace(item) for item in traces),
            safeguards=tuple(safeguards),
            diagnostics=dict(diagnostics or {}),
            generated_at=generated_at or datetime.now(timezone.utc),
        )
        payload = snapshot.as_payload()
        self._record(payload)
        return payload

    def _record(self, payload: Mapping[str, object]) -> None:
        if not self._collector or not self._context:
            return
        context = self._collector.annotate_session(self._context)
        allowed_fields = {"component", "generated_at", "metrics", "traces", "safeguards", "diagnostics"}
        self._collector.record(
            event_type="reflection.snapshot",
            context=context,
            payload=payload,
            allowed_fields=allowed_fields,
        )

    @staticmethod
    def _coerce_metric(item: ReflectionMetric | Mapping[str, object]) -> ReflectionMetric:
        if isinstance(item, ReflectionMetric):
            return item
        raw_value = item.get("value", 0)
        if isinstance(raw_value, (int, float)):
            numeric_value: float | int = raw_value
        else:
            try:
                numeric_value = float(raw_value)
            except Exception:  # pragma: no cover - defensive fall back
                numeric_value = 0.0
        return ReflectionMetric(
            key=str(item.get("key", "")),
            value=numeric_value,
            unit=item.get("unit"),
            info=item.get("info"),
        )

    @staticmethod
    def _coerce_trace(item: ReflectionTrace | Mapping[str, object]) -> ReflectionTrace:
        if isinstance(item, ReflectionTrace):
            return item
        detail_mapping = item.get("detail") if isinstance(item.get("detail"), Mapping) else {}
        return ReflectionTrace(
            event=str(item.get("event", "")),
            detail=dict(detail_mapping),
            level=str(item.get("level", "info")),
        )


__all__ = [
    "ReflectionMetric",
    "ReflectionTrace",
    "ReflectionSnapshot",
    "TransparentReflectionLayer",
]
