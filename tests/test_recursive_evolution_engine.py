"""Tests for the recursive evolution engine."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_engine() -> type:
    module_path = Path(__file__).resolve().parents[1] / "packages/core/src/echo/recursive_evolution_engine.py"
    spec = importlib.util.spec_from_file_location("echo_recursive_engine_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None  # for type checkers
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.RecursiveEvolutionEngine


RecursiveEvolutionEngine = _load_engine()


def _write_module(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_cycle_generates_snapshots_and_history(tmp_path):
    module_path = tmp_path / "demo_module.py"
    _write_module(
        module_path,
        """
def foo(value: int) -> int:
    if value > 2:
        return value * 2
    return value
""".strip(),
    )

    engine = RecursiveEvolutionEngine(modules=[module_path])

    first_report = engine.run_cycle()
    assert first_report.cycle_index == 1
    assert len(first_report.snapshots) == 1
    first_snapshot = first_report.snapshots[0]
    assert first_snapshot.function_count == 1
    assert first_snapshot.total_lines >= 4

    # Enrich the module with additional constructs to trigger new suggestions.
    _write_module(
        module_path,
        """
class Demo:
    def compute(self, data: list[int]) -> int:
        total = 0
        for item in data:
            if item % 2:
                total += item
            else:
                total -= item
        return total


def foo(value: int) -> int:
    match value:
        case 0:
            return 0
        case 1:
            return 1
        case _:
            return foo(value - 1) + foo(value - 2)
""".strip(),
    )

    second_report = engine.run_cycle()
    assert second_report.cycle_index == 2
    assert len(engine.history) == 2

    second_snapshot = second_report.snapshots[0]
    assert second_snapshot.class_count == 1
    assert second_snapshot.function_count >= first_snapshot.function_count
    assert second_snapshot.branching_complexity >= first_snapshot.branching_complexity

    # Ensure suggestions are propagated into the optimisation list.
    assert any("Demo" in action or "demo_module" in action for action in second_report.optimizations)
