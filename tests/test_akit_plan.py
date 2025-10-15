"""Tests for the autonomous plan runner."""

from __future__ import annotations

import json
from pathlib import Path

from akit.plan import AutonomousPlan, PlanRunner, verify_snapshot


def _make_plan(tmp_path) -> AutonomousPlan:
    return AutonomousPlan.from_dict(json.loads(json.dumps({
        "goals": ["demo"],
        "steps": [
            {"name": "step1", "action": "task"},
            {"name": "step2", "action": "task"},
        ],
        "safety_rules": [{"name": "baseline", "description": "ok"}],
        "max_cycles": 2,
        "budgets": {"time": 1},
    })))


def test_runner_creates_snapshots(tmp_path):
    plan = _make_plan(tmp_path)
    runner = PlanRunner(plan, dry_run=True, policy_check=lambda _: True)
    result = runner.run()
    assert result.steps_completed == 2
    for snapshot_path in result.snapshots:
        identifier = Path(snapshot_path).stem
        assert verify_snapshot(identifier)
        Path(snapshot_path).unlink()
    if result.checkpoint:
        Path(result.checkpoint).unlink()


def test_runner_guardrail_blocks_execution(tmp_path):
    plan = _make_plan(tmp_path)
    runner = PlanRunner(plan, dry_run=True, policy_check=lambda _: False)
    try:
        runner.run()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError")
