from __future__ import annotations

import pytest

from echo.memory.analytics import MemoryAnalytics
from echo.memory.store import ExecutionContext


def make_context(**overrides):
    base = dict(
        timestamp="2024-01-01T00:00:00+00:00",
        commands=[],
        dataset_fingerprints={},
        validations=[],
        metadata={},
        cycle=None,
        artifact=None,
        summary=None,
        metrics={},
    )
    base.update(overrides)
    return ExecutionContext(**base)


def test_command_frequency_and_validation_matrix():
    executions = [
        make_context(
            commands=[{"name": "advance"}, {"name": "advance"}],
            validations=[{"name": "integrity", "status": "pass"}],
        ),
        make_context(
            commands=[{"name": "advance"}, {"name": "summarize"}],
            validations=[
                {"name": "integrity", "status": "fail"},
                {"name": "consistency", "status": "pass"},
            ],
        ),
        make_context(commands=[{"name": "summarize"}, {"detail": "ignored"}]),
    ]

    analytics = MemoryAnalytics(executions)

    frequency = analytics.command_frequency()
    assert frequency == {"advance": 3, "summarize": 2}

    matrix = analytics.validation_matrix()
    summary_by_name = {entry.name: entry.outcomes for entry in matrix}
    assert summary_by_name == {
        "consistency": {"pass": 1},
        "integrity": {"fail": 1, "pass": 1},
    }


def test_metadata_index_and_timeline_report():
    executions = [
        make_context(
            timestamp="2024-02-01T12:00:00+00:00",
            cycle=1,
            metadata={"group": "alpha"},
            commands=[{"name": "start"}],
            summary="Initiated",
        ),
        make_context(
            timestamp="2024-02-02T12:00:00+00:00",
            cycle=2,
            metadata={"group": "beta"},
            commands=[{"name": "evaluate"}],
            summary="Evaluated",
        ),
        make_context(
            timestamp="2024-02-03T12:00:00+00:00",
            cycle=3,
            metadata={"group": "alpha", "note": "final"},
            commands=[{"name": "finalize"}],
            summary="Finalized",
        ),
    ]

    analytics = MemoryAnalytics(executions)

    metadata = analytics.metadata_index("group")
    assert metadata == [
        {"timestamp": "2024-02-01T12:00:00+00:00", "cycle": 1, "value": "alpha"},
        {"timestamp": "2024-02-02T12:00:00+00:00", "cycle": 2, "value": "beta"},
        {"timestamp": "2024-02-03T12:00:00+00:00", "cycle": 3, "value": "alpha"},
    ]

    timeline = analytics.timeline()
    assert timeline == [
        {
            "timestamp": "2024-02-01T12:00:00+00:00",
            "cycle": 1,
            "commands": ["start"],
            "summary": "Initiated",
        },
        {
            "timestamp": "2024-02-02T12:00:00+00:00",
            "cycle": 2,
            "commands": ["evaluate"],
            "summary": "Evaluated",
        },
        {
            "timestamp": "2024-02-03T12:00:00+00:00",
            "cycle": 3,
            "commands": ["finalize"],
            "summary": "Finalized",
        },
    ]

    report = analytics.as_markdown_report()
    assert "Total Executions: 3" in report
    assert "Command Frequency" in report
    assert "Validation Outcomes" not in report  # no validations recorded


def test_metadata_value_counts_handles_complex_values():
    executions = [
        make_context(metadata={"group": "alpha"}),
        make_context(metadata={"group": "alpha"}),
        make_context(metadata={"group": "beta"}),
        make_context(metadata={"group": {"name": "alpha", "level": 1}}),
        make_context(metadata={"group": {"level": 1, "name": "alpha"}}),
        make_context(metadata={"group": ["x", "y"]}),
        make_context(metadata={"group": ["x", "y"]}),
        make_context(metadata={"group": None}),
        make_context(metadata={"group": {"alpha"}}),
        make_context(metadata={"other": "ignored"}),
    ]

    analytics = MemoryAnalytics(executions)

    summary = analytics.metadata_value_counts("group")

    def find_value(predicate):
        for entry in summary:
            if predicate(entry.value):
                return entry
        raise AssertionError("value not found")

    assert find_value(lambda value: value == "alpha").count == 2
    assert find_value(lambda value: value == "beta").count == 1
    assert (
        find_value(
            lambda value: isinstance(value, dict)
            and value.get("name") == "alpha"
            and value.get("level") == 1
        ).count
        == 2
    )
    assert find_value(lambda value: isinstance(value, list) and value == ["x", "y"]).count == 2
    assert find_value(lambda value: value is None).count == 1
    assert find_value(lambda value: isinstance(value, set) and value == {"alpha"}).count == 1

    empty = analytics.metadata_value_counts("missing")
    assert empty == []


def test_metric_series_and_summary():
    executions = [
        make_context(
            timestamp="2024-03-01T00:00:00+00:00",
            cycle=1,
            metrics={
                "latency": [
                    {"value": 120.0, "unit": "ms", "recorded_at": "2024-03-01T00:00:01+00:00"}
                ],
                "notes": [
                    {"value": "warmup", "recorded_at": "2024-03-01T00:00:02+00:00", "metadata": {"phase": 1}}
                ],
            },
        ),
        make_context(
            timestamp="2024-03-02T00:00:00+00:00",
            cycle=2,
            metrics={
                "latency": [
                    {"value": 100, "unit": "ms", "recorded_at": "2024-03-02T00:00:01+00:00"},
                    {"value": 90, "unit": "ms", "recorded_at": "2024-03-02T00:00:02+00:00"},
                ]
            },
        ),
        make_context(
            timestamp="2024-03-03T00:00:00+00:00",
            cycle=3,
            metrics={"latency": [{"value": "n/a", "recorded_at": "2024-03-03T00:00:01+00:00"}]},
        ),
    ]

    analytics = MemoryAnalytics(executions)

    series = analytics.metric_series("latency")
    assert len(series) == 4
    assert series[0]["cycle"] == 1
    assert series[1]["value"] == 100
    assert series[2]["unit"] == "ms"
    assert series[3]["value"] == "n/a"

    summary = analytics.metric_summary("latency")
    assert summary == {"count": 3, "min": 90.0, "max": 120.0, "average": pytest.approx(103.3333333)}

    assert analytics.metric_summary("notes") is None
    assert analytics.metric_names() == ["latency", "notes"]

    report = analytics.as_markdown_report()
    assert "## Metrics" in report
    assert "latency" in report
