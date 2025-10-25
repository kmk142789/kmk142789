import pytest

from tools.pulse_anomaly_detector import (
    build_report,
    compute_interval_statistics,
    find_duplicate_hash_groups,
    find_interval_anomalies,
)
from tools.pulse_history_summary import PulseEvent


def _event(timestamp: float, message: str, hash_value: str) -> PulseEvent:
    return PulseEvent(timestamp=timestamp, message=message, hash=hash_value)


def test_compute_interval_statistics_returns_expected_values() -> None:
    events = [
        _event(0.0, "alpha", "h1"),
        _event(10.0, "beta", "h2"),
        _event(30.0, "gamma", "h3"),
    ]

    stats = compute_interval_statistics(events)
    assert stats is not None
    assert stats.mean == pytest.approx(15.0)
    assert stats.median == pytest.approx(15.0)
    assert stats.stdev == pytest.approx(5.0)
    assert stats.minimum == pytest.approx(10.0)
    assert stats.maximum == pytest.approx(20.0)


def test_find_interval_anomalies_flags_large_gap() -> None:
    events = [
        _event(0.0, "start", "h1"),
        _event(60.0, "normal", "h2"),
        _event(90.0, "normal", "h3"),
        _event(600.0, "late", "h4"),
    ]

    anomalies = find_interval_anomalies(events, z_threshold=1.0, minimum_gap=None)
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.start.message == "normal"
    assert anomaly.end.message == "late"
    assert anomaly.interval_seconds == pytest.approx(510.0)
    assert anomaly.z_score >= 1.0


def test_find_duplicate_hash_groups_returns_sorted_groups() -> None:
    events = [
        _event(0.0, "first", "dup"),
        _event(5.0, "second", "dup"),
        _event(10.0, "third", "unique"),
        _event(15.0, "fourth", "dup"),
    ]

    duplicates = find_duplicate_hash_groups(events)
    assert len(duplicates) == 1
    group = duplicates[0]
    assert group.hash == "dup"
    assert group.count == 3
    assert [event.message for event in group.events] == ["first", "second", "fourth"]


def test_build_report_includes_key_sections() -> None:
    events = [
        _event(0.0, "one", "a"),
        _event(5.0, "two", "b"),
        _event(15.0, "three", "c"),
    ]
    stats = compute_interval_statistics(events)
    anomalies = find_interval_anomalies(events, z_threshold=10.0, minimum_gap=9999)
    duplicates = find_duplicate_hash_groups(events)

    report = build_report(events, anomalies=anomalies, duplicates=duplicates, stats=stats)
    assert "Events analysed" in report
    assert "Interval anomalies" in report
    assert "Duplicate hashes" in report
    # No anomalies or duplicates should be reported for this dataset
    assert "None detected" in report
