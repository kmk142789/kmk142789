import time

from atlas_kernel import AtlasEventLoop, KernelDiagnostics, PriorityScheduler


def test_event_loop_priority_ordering():
    loop = AtlasEventLoop(scheduler=PriorityScheduler())
    execution = []

    loop.call_soon(lambda: execution.append("low"), priority=1, lane="low")
    loop.call_soon(lambda: execution.append("high"), priority=10, lane="high")
    loop.call_soon(loop.stop, priority=0)

    loop.run()

    assert execution[:2] == ["high", "low"]


def test_event_loop_records_diagnostics():
    diagnostics = KernelDiagnostics(window=8)
    loop = AtlasEventLoop(diagnostics=diagnostics)

    loop.call_soon(lambda: time.sleep(0.0), lane="alpha")
    loop.call_soon(loop.stop, lane="control", priority=0)

    loop.run()

    summary = diagnostics.summary()
    assert summary["events"] >= 1
    assert "alpha" in diagnostics.active_lanes()
