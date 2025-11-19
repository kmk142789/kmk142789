"""Tests for the digital time travel planner."""

from datetime import datetime, timedelta, timezone

import pytest

from echo.digital_time_travel import TimeTravelPlan, plan_digital_time_travel


def test_plan_digital_time_travel_forward() -> None:
    start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    target = start + timedelta(hours=2)

    plan = plan_digital_time_travel(start, target, hops=4, drift_ppm=20.0)

    assert isinstance(plan, TimeTravelPlan)
    assert plan.direction == "forward"
    assert plan.hop_count == 4
    assert len(plan.timeline) == 4
    assert plan.timeline[0].duration_seconds == pytest.approx(1800.0)
    assert plan.timeline[-1].end == target
    timeline_text = plan.render_timeline()
    assert "Digital time travel" in timeline_text


def test_plan_digital_time_travel_backward() -> None:
    start = datetime(2025, 1, 1, 3, 0, tzinfo=timezone.utc)
    target = datetime(2025, 1, 1, 1, 30, tzinfo=timezone.utc)

    plan = plan_digital_time_travel(start, target, hops=3, drift_ppm=10.0)

    assert plan.direction == "backward"
    assert plan.total_seconds == pytest.approx(-5400.0)
    assert plan.timeline[0].start > plan.timeline[0].end
    serialised = plan.as_dict()
    assert serialised["hop_count"] == 3
    assert serialised["timeline"][0]["duration_seconds"] == pytest.approx(1800.0)
