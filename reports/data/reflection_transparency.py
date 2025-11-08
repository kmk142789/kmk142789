"""Diagnostics collectors for the Transparent Reflection Layer."""
from __future__ import annotations

import json as json_lib
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReflectionDiagnostics:
    """Immutable diagnostics entry parsed from ``pulse_history.json``."""

    component: str
    metrics: Mapping[str, float | int]
    safeguards: Sequence[str]

    def as_payload(self) -> Mapping[str, object]:
        return {
            "component": self.component,
            "metrics": dict(self.metrics),
            "safeguards": list(self.safeguards),
        }


def load_reflection_diagnostics(path: Path) -> Sequence[ReflectionDiagnostics]:
    """Parse reflection diagnostics embedded in ``pulse_history.json``."""

    if not path.exists():
        return ()
    with path.open("r", encoding="utf-8") as handle:
        entries = json_lib.load(handle)
    diagnostics: list[ReflectionDiagnostics] = []
    for entry in entries:
        reflection = entry.get("reflection") if isinstance(entry, Mapping) else None
        if not reflection:
            continue
        component = str(reflection.get("component", ""))
        metrics_mapping = {
            key: value
            for key, value in reflection.get("metrics", {}).items()
            if isinstance(value, (int, float))
        }
        safeguards = [
            safeguard
            for safeguard in reflection.get("safeguards", [])
            if isinstance(safeguard, str)
        ]
        diagnostics.append(
            ReflectionDiagnostics(
                component=component,
                metrics=metrics_mapping,
                safeguards=tuple(safeguards),
            )
        )
    return tuple(diagnostics)


def summarise_reflection_metrics(diagnostics: Iterable[ReflectionDiagnostics]) -> Mapping[str, object]:
    """Aggregate diagnostics into a report suitable for publishing."""

    total_components = 0
    aggregated_metrics: MutableMapping[str, float] = {}
    safeguards: set[str] = set()
    for entry in diagnostics:
        if not entry.component:
            continue
        total_components += 1
        for key, value in entry.metrics.items():
            aggregated_metrics[key] = aggregated_metrics.get(key, 0.0) + float(value)
        safeguards.update(entry.safeguards)
    return {
        "components": total_components,
        "metrics": dict(sorted(aggregated_metrics.items())),
        "safeguards": sorted(safeguards),
    }


def build_reflection_report(
    *,
    pulse_history_path: Path,
    output_path: Path,
) -> Mapping[str, object]:
    """Collect diagnostics and persist a JSON report under ``reports/data``."""

    diagnostics = load_reflection_diagnostics(pulse_history_path)
    report = summarise_reflection_metrics(diagnostics)
    payload = {
        "snapshot": report,
        "entries": [entry.as_payload() for entry in diagnostics],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json_lib.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return payload


__all__ = [
    "ReflectionDiagnostics",
    "build_reflection_report",
    "load_reflection_diagnostics",
    "summarise_reflection_metrics",
]
