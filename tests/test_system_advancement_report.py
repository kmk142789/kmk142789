"""Tests for the :meth:`echo.evolver.EchoEvolver.system_advancement_report` helper."""

import pytest

from echo.evolver import EchoEvolver


def test_system_advancement_report_captures_state_and_events():
    evolver = EchoEvolver()

    evolver.advance_cycle()
    evolver.system_monitor()
    evolver.state.event_log.append("Custom event recorded")

    report = evolver.system_advancement_report(recent_events=2)

    assert f"cycle {evolver.state.cycle}" in report.lower()
    assert "Custom event recorded" in report
    assert "Recent events (showing 2" in report
    assert evolver.state.network_cache["system_advancement_report"] == report
    assert (
        evolver.state.event_log[-1]
        == "System advancement report generated (events_considered=2)"
    )
    completed = evolver.state.network_cache["completed_steps"]
    assert "system_advancement_report" in completed


def test_system_advancement_report_rejects_invalid_limits():
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.system_advancement_report(recent_events=0)

