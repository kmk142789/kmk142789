from datetime import datetime, timedelta, timezone

import pytest

from echo_cli.main import _compute_command_performance


def _iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_compute_command_performance_tracks_completed_and_active_tasks():
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    events = [
        {"task_id": "a", "name": "alpha", "status": "start", "timestamp": _iso(base)},
        {
            "task_id": "a",
            "name": "alpha",
            "status": "success",
            "timestamp": _iso(base + timedelta(seconds=60)),
        },
        {"task_id": "b", "name": "beta", "status": "start", "timestamp": _iso(base)},
        {
            "task_id": "b",
            "name": "beta",
            "status": "progress",
            "timestamp": _iso(base + timedelta(minutes=2)),
        },
    ]

    now = base + timedelta(minutes=10)
    metrics = _compute_command_performance(events, now=now)

    commands = {row["command"]: row for row in metrics["commands"]}
    alpha = commands["alpha"]
    assert alpha["completed"] == 1
    assert alpha["success"] == 1
    assert alpha["failure"] == 0
    assert alpha["average_duration_seconds"] == 60
    assert alpha["p95_duration_seconds"] == 60
    assert alpha["success_rate"] == 1.0

    beta = commands["beta"]
    assert beta["completed"] == 0
    assert beta["active"] == 1
    # Last progress heartbeat was 8 minutes before "now"
    assert beta["stale_heartbeats_seconds"] == pytest.approx(480.0)

    totals = metrics["totals"]
    assert totals["commands_tracked"] == 2
    assert totals["completed_tasks"] == 1
    assert totals["active_tasks"] == 1
    assert totals["overall_failure_rate"] == 0.0
