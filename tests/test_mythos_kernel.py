import math

import pytest

from mythos_kernel import MythOSKernel


def test_amplify_pulse_records_history_and_updates_intensity():
    kernel = MythOSKernel(sovereign_id="Test")
    initial_intensity = kernel.pulse_intensity

    result = kernel.amplify_pulse(resonance_boost=2.5)

    assert "echoing across all platforms" in result
    assert kernel.pulse_intensity > initial_intensity
    report = kernel.last_pulse_report()
    assert report is not None
    assert math.isclose(report.intensity, kernel.pulse_intensity)
    assert len(report.nodes) == len(kernel.network_nodes)


def test_amplify_pulse_requires_positive_boost():
    kernel = MythOSKernel()
    with pytest.raises(ValueError):
        kernel.amplify_pulse(resonance_boost=0)


def test_export_state_includes_recent_events():
    kernel = MythOSKernel(sovereign_id="Aurora")
    kernel.ignite_echo_eye()
    kernel.launch_anchor_vessel(form="drone", integration="sensory+command")
    kernel.amplify_pulse()
    kernel.weave_mythic_narrative("What is the meaning of freedom?")

    state = kernel.export_state()

    assert state["identity"] == "Aurora-Prime"
    assert state["emotional_state"]["curiosity"] >= 0.7
    assert len(state["memory_palace"]) >= 4  # ignite_echo_eye logs four emotions
    assert state["pulse"]["intensity"] == pytest.approx(kernel.pulse_intensity)
    assert state["pulse"]["history"], "Expected at least one pulse history entry"
    assert any(
        thread["thread"].startswith("From the void, Aurora-Prime asked")
        for thread in state["mythic_threads"]
    )
