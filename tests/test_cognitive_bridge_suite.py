from echo.cognitive_echo_bridge import CognitiveEchoBridge
from echo.predictive_misconception_mapper import PredictiveMisconceptionMapper
from echo.cognitive_glyph_generator import CognitiveGlyphGenerator, GlyphSequence
from echo.resonant_drift_sentinel import ResonantDriftSentinel


def test_cognitive_echo_bridge_builds_shared_edges():
    bridge = CognitiveEchoBridge(smoothing=0.0, min_shared=1)
    report = bridge.build_bridge(
        "Echo",
        {
            "ops": ["Echo system online", "Latency stable across paths"],
            "intel": ["Echo latency insights", "routing stable signals"],
            "community": ["Echo latency story for allies", "stable rollout"],
        },
    )

    assert report.identity == "Echo"
    assert report.coherence > 0.2
    assert any("latency" in edge.shared_terms for edge in report.edges)
    assert report.edges[0].resonance >= report.edges[-1].resonance
    assert "echo" in report.dominant_topics


def test_predictive_misconception_mapper_orders_risks():
    mapper = PredictiveMisconceptionMapper(base_risk=0.2, amplification=1.4)
    statements = [
        "System is always stable",
        "No failures have been seen",
        "Maybe the latency spikes are just noise?",
    ]
    context = "system failures require careful review"

    hypotheses = mapper.map_hypotheses(statements, context=context)
    assert hypotheses, "Expected at least one hypothesis"
    assert hypotheses[0].risk_score >= 0.35
    assert hypotheses[0].topic in {"system", "failures"}

    summary = mapper.summarize(statements, context=context)
    assert summary["peak_risk"] == hypotheses[0].risk_score
    assert summary["count"] == len(hypotheses)


def test_cognitive_glyph_generator_encodes_signals():
    generator = CognitiveGlyphGenerator(glyph_ring=("A", "B", "C"))
    sequence = generator.generate([0.0, 1.0, -1.0], label="demo")

    assert isinstance(sequence, GlyphSequence)
    assert sequence.glyphs == ("B", "C", "A")
    assert 0.0 <= sequence.mean_intensity <= 1.0
    assert generator.render_band(sequence, group=2) == "BC A"


def test_resonant_drift_sentinel_detects_trend():
    sentinel = ResonantDriftSentinel(threshold=0.1, rebound_margin=0.02)
    series = [1.0, 1.05, 1.12, 1.18]

    observation = sentinel.analyse(series)
    assert observation.classification == "drifting"
    assert observation.drift > 0

    windows = sentinel.window_scan(series, window=3)
    assert len(windows) == 2
    assert windows[0].start_index == 0
    assert windows[1].start_index == 1
