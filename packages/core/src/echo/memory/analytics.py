"""Analytical helpers for summarizing Echo memory executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .store import ExecutionContext, JsonMemoryStore


@dataclass(slots=True)
class ValidationSummary:
    """Aggregated validation counts for a specific validation name."""

    name: str
    outcomes: Dict[str, int]


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

        return "".join(lines)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def executions(self) -> List[ExecutionContext]:
        """Return the underlying executions as a list copy."""

        return list(self._executions)


__all__ = ["MemoryAnalytics", "ValidationSummary"]
