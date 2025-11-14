"""Tests for EchoEvolver.advance_system_history_report."""

from echo.evolver import EchoEvolver


def test_history_report_handles_empty_cache() -> None:
    evolver = EchoEvolver()

    report = evolver.advance_system_history_report()

    assert "No advance-system history" in report
    assert evolver.state.network_cache["advance_system_history_report"] == report
    assert (
        evolver.state.event_log[-1]
        == "Advance system history report generated (entries=0, limit=None)"
    )


def test_history_report_summarises_entries_and_respects_limit() -> None:
    evolver = EchoEvolver()
    evolver.state.network_cache["advance_system_history"] = [
        {
            "cycle": 1,
            "progress_percent": 25.0,
            "momentum": 0.05,
            "expansion": {"phase": "expanding"},
        },
        {
            "cycle": 2,
            "progress_percent": 62.5,
            "momentum": -0.03,
            "expansion": {"phase": "steady"},
        },
    ]

    report = evolver.advance_system_history_report(limit=1)

    assert "entries=1" in report
    assert "Cycle 2" in report
    assert "Cycle 1" not in report
    assert "phase steady" in report
    assert "momentum -0.030 (regressing)" in report
    assert evolver.state.network_cache["advance_system_history_report"] == report
    assert (
        evolver.state.event_log[-1]
        == "Advance system history report generated (entries=1, limit=1)"
    )
