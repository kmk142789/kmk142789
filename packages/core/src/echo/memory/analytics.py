"""Analytical helpers for summarizing Echo memory executions."""

from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .store import ExecutionContext, JsonMemoryStore


@dataclass(slots=True)
class ValidationSummary:
    """Aggregated validation counts for a specific validation name."""

    name: str
    outcomes: Dict[str, int]


@dataclass(slots=True)
class MetadataValueCount:
    """Count of how frequently a metadata value appears across executions."""

    value: Any
    count: int


class MemoryAnalytics:
    """Compute derived insights from stored :class:`ExecutionContext` objects.

    Parameters
    ----------
    executions:
        Sequence of execution contexts ordered chronologically.
    """

    def __init__(self, executions: Sequence[ExecutionContext]):
        self._executions: List[ExecutionContext] = list(executions)

    @classmethod
    def from_store(
        cls,
        store: JsonMemoryStore,
        *,
        limit: Optional[int] = None,
        metadata_filter: Optional[Mapping[str, Any]] = None,
    ) -> "MemoryAnalytics":
        """Create an analytics helper from a :class:`JsonMemoryStore`.

        Parameters
        ----------
        store:
            Memory store containing execution history.
        limit:
            Optional maximum number of executions to include. Delegated to
            :meth:`JsonMemoryStore.recent_executions`.
        metadata_filter:
            Optional metadata constraint for selecting executions.
        """

        executions = store.recent_executions(limit=limit, metadata_filter=metadata_filter)
        return cls(executions)

    # ------------------------------------------------------------------
    # Aggregate views
    # ------------------------------------------------------------------
    def command_frequency(self) -> Dict[str, int]:
        """Return a frequency table of command names across executions."""

        counts: Counter[str] = Counter()
        for context in self._executions:
            for command in context.commands:
                name = command.get("name")
                if name:
                    counts[name] += 1
        return dict(counts)

    def validation_matrix(self) -> List[ValidationSummary]:
        """Return aggregated validation outcomes grouped by validation name."""

        matrix: Dict[str, Counter[str]] = defaultdict(Counter)
        for context in self._executions:
            for result in context.validations:
                name = result.get("name")
                status = result.get("status", "unknown")
                if name:
                    matrix[name][status] += 1
        summaries = [
            ValidationSummary(name=name, outcomes=dict(outcomes))
            for name, outcomes in sorted(matrix.items())
        ]
        return summaries

    def metadata_index(self, key: str) -> List[Dict[str, Any]]:
        """Return timeline-aligned metadata values for ``key``."""

        entries: List[Dict[str, Any]] = []
        for context in self._executions:
            if key in context.metadata:
                entries.append(
                    {
                        "timestamp": context.timestamp,
                        "cycle": context.cycle,
                        "value": context.metadata[key],
                    }
                )
        return entries

    def metadata_value_counts(self, key: str) -> List[MetadataValueCount]:
        """Return frequency counts for distinct metadata values associated with ``key``.

        The method is resilient to unhashable values such as dictionaries or lists by
        internally normalising them with a canonical string representation while still
        returning the original value (copied when necessary) to the caller.
        """

        buckets: Dict[str, MetadataValueCount] = {}
        for context in self._executions:
            if key not in context.metadata:
                continue
            raw_value = context.metadata[key]
            canonical = self._canonical_metadata_value(raw_value)
            entry = buckets.get(canonical)
            if entry is None:
                buckets[canonical] = MetadataValueCount(
                    value=self._preserve_metadata_value(raw_value),
                    count=1,
                )
            else:
                entry.count += 1

        ordered: List[Tuple[str, MetadataValueCount]] = sorted(
            buckets.items(), key=lambda item: (-item[1].count, item[0])
        )
        return [entry for _, entry in ordered]

    def timeline(self) -> List[Dict[str, Any]]:
        """Return a simplified timeline of executions."""

        return [
            {
                "timestamp": context.timestamp,
                "cycle": context.cycle,
                "commands": [command.get("name") for command in context.commands if command.get("name")],
                "summary": context.summary,
            }
            for context in self._executions
        ]

    def metric_series(self, name: str) -> List[Dict[str, Any]]:
        """Return a chronological series of samples for ``name``.

        Each entry contains the execution timestamp, cycle number (if available)
        and the recorded metric payload for the requested metric.
        """

        series: List[Dict[str, Any]] = []
        for context in self._executions:
            samples = context.metrics.get(name, [])
            for sample in samples:
                payload = {
                    "timestamp": context.timestamp,
                    "cycle": context.cycle,
                    "value": sample.get("value"),
                    "recorded_at": sample.get("recorded_at"),
                }
                if "unit" in sample:
                    payload["unit"] = sample["unit"]
                if "metadata" in sample:
                    payload["metadata"] = sample["metadata"]
                series.append(payload)
        return series

    def metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Return aggregate statistics for numeric samples of ``name``.

        Non-numeric metric values are ignored. When no numeric samples are
        present ``None`` is returned.
        """

        numeric_values: List[float] = []
        for entry in self.metric_series(name):
            value = entry.get("value")
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))

        if not numeric_values:
            return None

        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "average": mean(numeric_values),
        }

    def metric_names(self) -> List[str]:
        """Return a sorted list of metric identifiers present in executions."""

        names = {name for context in self._executions for name in context.metrics if context.metrics.get(name)}
        return sorted(names)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def as_markdown_report(self) -> str:
        """Render an at-a-glance Markdown summary of the execution history."""

        lines = ["# Echo Memory Summary", ""]
        lines.append(f"Total Executions: {len(self._executions)}\n")

        command_stats = self.command_frequency()
        if command_stats:
            lines.append("## Command Frequency\n")
            for name, count in sorted(command_stats.items(), key=lambda item: (-item[1], item[0])):
                lines.append(f"- {name}: {count}\n")
            lines.append("\n")

        validations = self.validation_matrix()
        if validations:
            lines.append("## Validation Outcomes\n")
            for summary in validations:
                outcomes = ", ".join(f"{status}: {count}" for status, count in sorted(summary.outcomes.items()))
                lines.append(f"- {summary.name}: {outcomes}\n")
            lines.append("\n")

        metric_names = self.metric_names()
        if metric_names:
            lines.append("## Metrics\n")
            for metric_name in metric_names:
                summary = self.metric_summary(metric_name)
                if summary:
                    lines.append(
                        "- {name}: count={count}, min={min:.3f}, max={max:.3f}, average={avg:.3f}\n".format(
                            name=metric_name,
                            count=summary["count"],
                            min=summary["min"],
                            max=summary["max"],
                            avg=summary["average"],
                        )
                    )
                else:
                    lines.append(f"- {metric_name}: non-numeric samples\n")
            lines.append("\n")

        return "".join(lines)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def executions(self) -> List[ExecutionContext]:
        """Return the underlying executions as a list copy."""

        return list(self._executions)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _canonical_metadata_value(value: Any) -> str:
        """Return a canonical string for grouping metadata values."""

        primitive_types = (str, int, float, bool)
        if value is None or isinstance(value, primitive_types):
            return f"{type(value).__name__}:{value!r}"

        try:
            serialised = json.dumps(
                value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            return f"{type(value).__name__}:{serialised}"
        except TypeError:
            return f"{type(value).__name__}:{repr(value)}"

    @staticmethod
    def _preserve_metadata_value(value: Any) -> Any:
        """Return a safe copy of ``value`` for inclusion in analytics results."""

        try:
            return copy.deepcopy(value)
        except TypeError:
            return value


__all__ = ["MemoryAnalytics", "MetadataValueCount", "ValidationSummary"]
