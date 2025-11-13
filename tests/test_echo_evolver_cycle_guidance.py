"""Tests for cycle guidance helpers on :class:`echo.evolver.EchoEvolver`."""

from echo.evolver import CycleGuidanceFrame, EchoEvolver


def test_cycle_guidance_frame_records_snapshot_and_cache():
    evolver = EchoEvolver()

    frame = evolver.cycle_guidance_frame(momentum_samples=2, recent_events=1)

    assert isinstance(frame, CycleGuidanceFrame)
    assert frame.cycle == evolver.state.cycle
    assert frame.progress_percent == 0.0
    assert frame.pending_steps[0] == "advance_cycle"
    assert frame.scope_directives[frame.focus_scope]
    assert evolver.state.network_cache["cycle_guidance_frame"] == frame.as_dict()
    assert "Cycle guidance frame generated" in evolver.state.event_log[-1]


def test_cycle_guidance_summary_exports_human_readable_message():
    evolver = EchoEvolver()
    evolver.advance_cycle()

    summary = evolver.cycle_guidance_summary(momentum_samples=1, recent_events=2)

    assert "EchoEvolver cycle guidance" in summary
    assert f"cycle {evolver.state.cycle}" in summary.lower()
    assert "Next step:" in summary
    assert evolver.state.network_cache["cycle_guidance_summary"] == summary
    assert "Cycle guidance summary broadcast" in evolver.state.event_log[-1]
