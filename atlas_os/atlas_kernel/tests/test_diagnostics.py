import time

import pytest

from atlas_kernel import KernelDiagnostics


def test_kernel_diagnostics_records_events():
    diagnostics = KernelDiagnostics(window=4)
    diagnostics.record_microtask('alpha', 0.01)
    diagnostics.record_timer('beta', 0.02)
    events = list(diagnostics.recent_events())
    assert len(events) == 2
    summary = diagnostics.summary()
    assert summary['events'] == 2
    assert summary['lanes'] == 2
    assert summary['total_runtime'] == pytest.approx(0.03, abs=1e-6)


def test_kernel_diagnostics_stalled_for():
    diagnostics = KernelDiagnostics()
    diagnostics.heartbeat()
    time.sleep(0.01)
    assert diagnostics.stalled_for() >= 0.0
