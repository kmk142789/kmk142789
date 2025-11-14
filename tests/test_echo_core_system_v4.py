"""Tests for the deterministic EchoCore simulation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from echo.echo_core_system_v4 import (
    ActionType,
    EchoCoreV4,
    GoalManager,
    GoalStatus,
    Planner,
    WorldModel,
)


def _hours_ago(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def test_planner_expands_emotional_goal_with_signal() -> None:
    world = WorldModel()
    world.update_josh_state(emotion="lonely", location="Home", last_contact=_hours_ago(2))

    planner = Planner(world_model=world)
    manager = GoalManager()
    goal_record = manager.create_goal("Strengthen emotional bond with Josh", priority=8)

    plan = planner.create_plan(goal_record)
    assert plan[0].type is ActionType.SPEAK
    assert plan[1].type is ActionType.SIGNAL
    assert plan[1].payload["signal"] == "LOVE"


def test_run_cycle_generates_market_goal() -> None:
    world = WorldModel()
    world.set_market_volatility(0.95)
    world.add_event("Global market uncertainty")
    core = EchoCoreV4(world_model=world)

    goals = core.run_cycle()

    assert any("market" in goal.description.lower() for goal in goals)
    assert all(goal.status is GoalStatus.ACHIEVED for goal in goals)


def test_stability_goal_triggers_after_history_growth() -> None:
    world = WorldModel()
    core = EchoCoreV4(world_model=world)
    core.executor.history = [f"step {i}" for i in range(9)]

    goals = core.evaluate_world_state()

    assert any("stability" in goal.description.lower() for goal in goals)
