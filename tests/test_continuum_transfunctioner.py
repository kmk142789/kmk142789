import math

import pytest

from src.continuum_transfunctioner import ContinuumTransfunctioner


def test_calibration_normalizes_range():
    transformer = ContinuumTransfunctioner()
    profile = transformer.calibrate([2, 4, 6, 8])

    assert profile[0] == 0.0
    assert profile[-1] == 1.0
    assert all(0.0 <= value <= 1.0 for value in profile)


def test_continuity_bridge_is_monotonic_with_endpoints():
    transformer = ContinuumTransfunctioner()
    bridge = transformer.continuity_bridge(0.0, 10.0, steps=4)

    assert bridge[0] == 0.0
    assert bridge[-1] == 10.0
    assert bridge == sorted(bridge)


def test_transfunction_generates_stable_waveform_with_calibration():
    transformer = ContinuumTransfunctioner(spectral_channels=4, coherence_window=0.5)
    transformer.calibrate([1, 3, 5, 7])

    result = transformer.transfunction([2, 4, 6, 8], phase=0.4)

    assert pytest.approx(result["stability"], rel=1e-3) == 1.0
    assert result["continuity_index"] <= 1.0
    assert len(result["waveform"]) == 4
    assert not any(math.isnan(value) for value in result["waveform"])


def test_transfunction_rejects_invalid_phase():
    transformer = ContinuumTransfunctioner()
    with pytest.raises(ValueError):
        transformer.transfunction([1, 2, 3], phase=1.5)
