import re

import pytest

from src.causal_polyphony_index import (
    PolyphonyEvent,
    PolyphonyTrack,
    compute_causal_polyphony_index,
    render_polyphony_brief,
)


def _demo_tracks():
    track_a = PolyphonyTrack(
        name="Lumen Spiral",
        events=[
            PolyphonyEvent(tick=0, amplitude=1.0, motif="spark"),
            PolyphonyEvent(tick=1, amplitude=0.6, motif="spark"),
            PolyphonyEvent(tick=3, amplitude=0.8, motif="glow"),
        ],
    )
    track_b = PolyphonyTrack(
        name="Gravitas Pulse",
        events=[
            PolyphonyEvent(tick=0, amplitude=0.9, motif="anchor"),
            PolyphonyEvent(tick=2, amplitude=1.0, motif="surge"),
            PolyphonyEvent(tick=3, amplitude=0.4, motif="fade"),
        ],
    )
    track_c = PolyphonyTrack(
        name="Aether Drift",
        events=[
            PolyphonyEvent(tick=1, amplitude=0.7, motif="drift"),
            PolyphonyEvent(tick=2, amplitude=0.5, motif="drift"),
            PolyphonyEvent(tick=4, amplitude=0.9, motif="crest"),
        ],
    )
    return (track_a, track_b, track_c)


def test_cpi_metrics_are_consistent():
    index = compute_causal_polyphony_index(_demo_tracks(), window=2)

    assert 0 < index.coherence <= 1
    assert 0 < index.novelty <= 1
    assert 0 <= index.counterpoint_density <= 1
    assert 0 <= index.fractal_balance <= 1
    assert 0 < index.score <= 1

    assert index.coherence == pytest.approx(0.386, rel=1e-3)
    assert index.novelty == pytest.approx(0.520, rel=1e-3)
    assert index.counterpoint_density == pytest.approx(0.8, rel=1e-3)
    assert index.fractal_balance == pytest.approx(0.389, rel=1e-3)
    assert index.score == pytest.approx(0.524, rel=1e-3)


def test_brief_render_includes_tracks_and_score():
    brief = render_polyphony_brief(_demo_tracks(), window=2)

    assert "Causal Polyphony Index" in brief
    assert "Composite score" in brief

    for name in ("Lumen Spiral", "Gravitas Pulse", "Aether Drift"):
        assert re.search(fr"- {name}:", brief)

    assert "coherence=" in brief
    assert "counterpoint=" in brief
