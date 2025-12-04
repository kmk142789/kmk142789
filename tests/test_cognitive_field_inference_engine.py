import numpy as np

from echo.cognitive_field_inference_engine import CFIEngine, SignalFusion


def test_engine_step_produces_forecast():
    engine = CFIEngine(rng=np.random.default_rng(0), noise_scale=0.0)
    output = engine.step({"keystroke_variance": 0.5, "cursor_entropy": 0.3, "task_delta": 0.2})

    assert set(output.keys()) == {"manifold", "features", "forecast", "encoded_vector"}
    assert "overload_risk" in output["forecast"]
    assert len(output["manifold"]["state"]) == 8
    assert np.isfinite(output["manifold"]["curvature"])


def test_overload_triggered_with_high_signals():
    engine = CFIEngine(rng=np.random.default_rng(0), noise_scale=0.0)
    signals = {
        "keystroke_variance": 4.0,
        "cursor_entropy": 4.0,
        "attention_shift": 3.5,
        "task_delta": 2.0,
        "hesitation_index": 1.5,
        "conflict_metric": 2.5,
        "tempo_ratio": 2.0,
    }

    output = engine.step(signals)
    assert output["forecast"]["overload_risk"] is True


def test_attention_drift_detects_shift_over_time():
    engine = CFIEngine(rng=np.random.default_rng(0), noise_scale=0.0)
    engine.step({"keystroke_variance": 0.2, "cursor_entropy": 0.1, "attention_shift": 0.05})
    output = engine.step({"keystroke_variance": 1.2, "cursor_entropy": 1.1, "attention_shift": 1.4})

    assert output["forecast"]["attention_drift"] is True


def test_signal_fusion_shape_is_consistent():
    fusion = SignalFusion(rng=np.random.default_rng(0), noise_scale=0.0)
    vector = fusion.fuse({})

    assert vector.shape == (8,)
    assert vector[-1] == 1.0  # tempo_ratio default
