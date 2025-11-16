"""Recursive module evolution planning engine.

The :class:`RecursiveEvolutionEngine` analyses a curated list of modules and
records a narrative about how the codebase changes over time.  Instead of
mutating files directly (which would be unsafe inside automated tests), the
engine builds an optimisation roadmap by comparing structural metrics – line
counts, branching complexity, TODO markers, and the ratio of classes to
functions – for every cycle.  Downstream tooling such as :mod:`echo.evolver`
can subscribe to the generated :class:`CycleReport` instances and decide how to
implement the suggested refactors.

This module deliberately keeps the implementation lightweight so it can run in
restricted environments (e.g. CI or read-only sandboxes).  It relies on the
standard library only and keeps state in memory, making it safe to instantiate
multiple times inside a single process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import ast
import logging
import time
from pathlib import Path
from typing import Callable, Iterable, List, Sequence

logger = logging.getLogger(__name__)


@dataclass
class ModuleSnapshot:
    """Description of a module during a single evolution cycle."""

    name: str
    path: Path
    total_lines: int
    function_count: int
    class_count: int
    branching_complexity: int
    todo_markers: int
    suggestions: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        """Return a serialisable representation of the snapshot."""

        return {
            "name": self.name,
            "path": str(self.path),
            "total_lines": self.total_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "branching_complexity": self.branching_complexity,
            "todo_markers": self.todo_markers,
            "suggestions": list(self.suggestions),
        }


@dataclass
class CycleReport:
    """Summary of a single recursive evolution cycle."""

    cycle_index: int
    duration_s: float
    snapshots: Sequence[ModuleSnapshot]
    optimizations: Sequence[str]

    def as_dict(self) -> dict:
        """Return a serialisable view of the report."""

        return {
            "cycle_index": self.cycle_index,
            "duration_s": self.duration_s,
            "snapshots": [snapshot.as_dict() for snapshot in self.snapshots],
            "optimizations": list(self.optimizations),
        }


class RecursiveEvolutionEngine:
    """Continuously analyse and optimise modules across recursive cycles.

    Parameters
    ----------
    modules:
        Sequence of modules (as ``Path`` objects or path-like strings) that
        should be inspected on every cycle.  The engine resolves paths relative
        to ``root`` if the provided value is not absolute.
    root:
        Optional base directory used when resolving module paths.
    on_cycle:
        Optional callback invoked after each cycle with the resulting
        :class:`CycleReport`.  The callback can persist the report or trigger
        additional automation (e.g. running :class:`echo.evolver.EchoEvolver`).
    """

    def __init__(
        self,
        *,
        modules: Iterable[str | Path] | None = None,
        root: str | Path | None = None,
        on_cycle: Callable[[CycleReport], None] | None = None,
    ) -> None:
        self.root = Path(root) if root is not None else Path.cwd()
        self._modules: List[Path] = []
        self._cycle_index = 0
        self._history: List[CycleReport] = []
        self._on_cycle = on_cycle

        for module in modules or []:
            self.add_module(module)

    @property
    def modules(self) -> Sequence[Path]:
        """Return the registered module paths."""

        return tuple(self._modules)

    @property
    def history(self) -> Sequence[CycleReport]:
        """Return the accumulated cycle reports."""

        return tuple(self._history)

    def add_module(self, module: str | Path) -> Path:
        """Register a module for inspection and return its resolved path."""

        path = Path(module)
        if not path.is_absolute():
            path = (self.root / path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Module path {path!s} does not exist")

        if path not in self._modules:
            self._modules.append(path)
            logger.debug("Registered module for recursion: %s", path)
        return path

    def run_cycle(self) -> CycleReport:
        """Inspect every module and produce a :class:`CycleReport`."""

        if not self._modules:
            raise RuntimeError("No modules registered for recursive evolution")

        self._cycle_index += 1
        start = time.perf_counter()

        previous_snapshots = {
            snapshot.name: snapshot
            for snapshot in self._history[-1].snapshots
        } if self._history else {}

        snapshots: List[ModuleSnapshot] = []
        for path in self._modules:
            snapshot = self._inspect_module(path)
            previous = previous_snapshots.get(snapshot.name)
            snapshot.suggestions.extend(self._suggest_improvements(snapshot, previous))
            snapshots.append(snapshot)

        optimizations = self._compile_optimizations(snapshots)
        duration = time.perf_counter() - start
        report = CycleReport(
            cycle_index=self._cycle_index,
            duration_s=duration,
            snapshots=tuple(snapshots),
            optimizations=tuple(optimizations),
        )
        self._history.append(report)

        logger.info(
            "Recursive evolution cycle %s finished in %.3fs with %s optimizations",
            report.cycle_index,
            report.duration_s,
            len(report.optimizations),
        )

        if self._on_cycle is not None:
            self._on_cycle(report)

        return report

    def continuous_run(self, cycles: int, *, delay_s: float = 0.0) -> Sequence[CycleReport]:
        """Run multiple cycles, optionally pausing between iterations."""

        reports = []
        for _ in range(cycles):
            reports.append(self.run_cycle())
            if delay_s:
                time.sleep(delay_s)
        return tuple(reports)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _inspect_module(self, path: Path) -> ModuleSnapshot:
        source = path.read_text(encoding="utf-8")
        total_lines = source.count("\n") + 1
        tree = ast.parse(source, filename=str(path))

        function_count = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
        class_count = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        branching_complexity = self._estimate_branching_complexity(tree)
        todo_markers = source.upper().count("TODO")

        snapshot = ModuleSnapshot(
            name=path.stem,
            path=path,
            total_lines=total_lines,
            function_count=function_count,
            class_count=class_count,
            branching_complexity=branching_complexity,
            todo_markers=todo_markers,
        )
        return snapshot

    def _estimate_branching_complexity(self, tree: ast.AST) -> int:
        branching_nodes = (
            ast.If,
            ast.For,
            ast.AsyncFor,
            ast.While,
            ast.Try,
            ast.With,
            ast.BoolOp,
            ast.IfExp,
        )
        match_node = getattr(ast, "Match", None)
        if match_node is not None:  # pragma: no cover - Py<3.10 compatibility
            branching_nodes = branching_nodes + (match_node,)

        return sum(isinstance(node, branching_nodes) for node in ast.walk(tree))

    def _suggest_improvements(self, snapshot: ModuleSnapshot, previous: ModuleSnapshot | None) -> List[str]:
        suggestions: List[str] = []

        if snapshot.total_lines > 500:
            suggestions.append("Split large module into themed submodules")
        elif snapshot.total_lines < 100:
            suggestions.append("Module is lean; ensure it remains cohesive")

        if snapshot.branching_complexity > max(20, snapshot.total_lines // 5):
            suggestions.append("Reduce branching complexity with helper functions")

        if snapshot.todo_markers:
            suggestions.append(f"Resolve {snapshot.todo_markers} TODO markers")

        if snapshot.class_count == 0 and snapshot.function_count > 10:
            suggestions.append("Introduce data classes to group related behaviour")

        if previous is not None:
            if snapshot.branching_complexity > previous.branching_complexity:
                suggestions.append("Complexity increased; schedule refactor")
            elif snapshot.branching_complexity < previous.branching_complexity:
                suggestions.append("Complexity decreased; capture learnings")

            if snapshot.total_lines - previous.total_lines > 200:
                suggestions.append("Rapid growth detected; document new surfaces")

        if not suggestions:
            suggestions.append("Module stable; continue optimisation review next cycle")

        return suggestions

    def _compile_optimizations(self, snapshots: Sequence[ModuleSnapshot]) -> List[str]:
        actions: List[str] = []
        for snapshot in snapshots:
            for suggestion in snapshot.suggestions:
                actions.append(f"{snapshot.name}: {suggestion}")

        if not actions:
            actions.append("All modules remain stable; nothing to optimise this cycle")

        return actions


__all__ = [
    "RecursiveEvolutionEngine",
    "CycleReport",
    "ModuleSnapshot",
]

