"""Regression tests for the newly added progressive features."""
from datetime import datetime, timezone

from echo_cli.progressive_features import (
    plan_capacity_allocation,
    simulate_portfolio_outcomes,
)


def test_plan_capacity_allocation_basic():
    capacities = {"core": 40, "ml": 32}
    tasks = [
        {"name": "API polish", "team": "core", "effort": 16, "priority": 2},
        {"name": "Auth hardening", "team": "core", "effort": 32, "priority": 1},
        {"name": "Model refresh", "team": "ml", "effort": 28, "priority": 2},
    ]
    payload = plan_capacity_allocation(capacities, tasks, cycle_length_days=7)
    assert payload["summary"]["total_tasks"] == 3
    assert payload["summary"]["cycle_length_days"] == 7
    assert payload["teams"]["core"]["cycles_required"] == 2
    assert payload["teams"]["ml"]["load_factor"] > 0.8
    assert not payload["unassigned"]


def test_simulate_portfolio_outcomes_rollup():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    initiatives = [
        {
            "name": "Alpha",
            "weight": 2,
            "milestones": [
                {"name": "Design", "duration": 5, "confidence": 0.9},
                {"name": "Build", "duration": 10, "confidence": 0.85},
            ],
        },
        {
            "name": "Beta",
            "weight": 1,
            "milestones": [
                {"name": "Discovery", "duration": 4, "confidence": 0.95},
            ],
        },
    ]
    payload = simulate_portfolio_outcomes(initiatives, start=start)
    assert payload["portfolio"]["critical_path"] in {"Alpha", "Beta"}
    assert payload["portfolio"]["risk_index"] >= 1
    assert len(payload["initiatives"]) == 2
