from __future__ import annotations

import pytest

from echo.evolver import EchoEvolver


def _ticking_time_source():
    counter = {"value": 0}

    def tick() -> int:
        counter["value"] += 1
        return counter["value"]

    return tick


def test_step_completion_report_tracks_cycles_and_occurrences():
    evolver = EchoEvolver(time_source=_ticking_time_source())

    evolver.advance_cycle()
    evolver.mutate_code()
    evolver.emotional_modulation()

    evolver.advance_cycle()
    evolver.mutate_code()

    report = evolver.step_completion_report()

    assert report["cycles_considered"][-1] == evolver.state.cycle
    mutate_row = next(row for row in report["rows"] if row["step"] == "mutate_code")
    assert mutate_row["occurrences"] == 2
    assert mutate_row["cycles"] == [1, 2]
    assert mutate_row["first_timestamp_ns"] <= mutate_row["last_timestamp_ns"]
    assert mutate_row["age_ns"] is not None
    assert (
        evolver.state.network_cache["step_completion_report"]["unique_steps"]
        == report["unique_steps"]
    )


def test_step_completion_report_window_and_age_controls():
    evolver = EchoEvolver(time_source=_ticking_time_source())

    evolver.advance_cycle()
    evolver.mutate_code()

    report = evolver.step_completion_report(cycles=[1], include_age=False)
    mutate_row = next(row for row in report["rows"] if row["step"] == "mutate_code")
    assert mutate_row["age_ns"] is None

    evolver.advance_cycle()
    evolver.mutate_code()

    recent_report = evolver.step_completion_report(window=1)
    assert recent_report["cycles_considered"] == [2]

    with pytest.raises(ValueError):
        evolver.step_completion_report(window=0)
