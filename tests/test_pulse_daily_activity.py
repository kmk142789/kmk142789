from datetime import datetime, timezone

import pytest

from tools.pulse_daily_activity import (
    DailyActivity,
    calculate_daily_activity,
    render_activity_table,
)


def test_calculate_daily_activity_basic():
    entries = [
        {"timestamp": datetime(2024, 1, 1, 12, tzinfo=timezone.utc).timestamp()},
        {"timestamp": datetime(2024, 1, 1, 18, tzinfo=timezone.utc).timestamp()},
        {"timestamp": datetime(2024, 1, 2, 8, tzinfo=timezone.utc).timestamp()},
        {"timestamp": datetime(2024, 1, 3, 9, tzinfo=timezone.utc).timestamp()},
        {"timestamp": datetime(2024, 1, 3, 11, tzinfo=timezone.utc).timestamp()},
        {"timestamp": datetime(2024, 1, 3, 19, tzinfo=timezone.utc).timestamp()},
    ]

    summary = calculate_daily_activity(entries)

    assert summary.total_entries == 6
    assert summary.total_days == 3
    assert summary.busiest_day == DailyActivity(date="2024-01-03", count=3)
    assert summary.quietest_day == DailyActivity(date="2024-01-02", count=1)
    assert [item.count for item in summary.activity] == [2, 1, 3]


def test_calculate_daily_activity_invalid_timestamp():
    entries = [{"timestamp": "not-a-number"}]

    with pytest.raises(ValueError):
        calculate_daily_activity(entries)


def test_render_activity_table_scaling():
    activity = [
        DailyActivity(date="2024-01-01", count=1),
        DailyActivity(date="2024-01-02", count=3),
    ]

    table = render_activity_table(activity, width=6, bar_char="#")
    lines = table.splitlines()

    assert lines[0].startswith("2024-01-01 |   1 ")
    assert lines[1].startswith("2024-01-02 |   3 ")
    # The busiest day should use the full width, while smaller days scale accordingly.
    assert lines[1].endswith("######")
    assert 0 < len(lines[0].split()[-1]) < len(lines[1].split()[-1])


def test_render_activity_table_no_entries():
    assert render_activity_table([], width=4) == "(no activity)"
