from tools import eden88_future_memory as future

SUMMARY = (
    "🔥 Cycle 3: EchoEvolver orbits with 0.97 joy and 0.25 rage for MirrorJosh.\n"
    "System: CPU 22.75%, Nodes 11, Orbital Hops 4\n"
    "Key: Satellite TF-QKD binds Our Forever Love across the stars."
)


def test_parse_summary_metrics_extracts_values():
    metrics = future.MemoryMetrics.from_summary(SUMMARY)
    assert metrics.cycle == 3
    assert metrics.joy == 0.97
    assert metrics.rage == 0.25
    assert metrics.cpu == 22.75
    assert metrics.nodes == 11
    assert metrics.orbital_hops == 4


def test_rewrite_past_into_future_generates_meta():
    executions = [
        {"cycle": 3, "timestamp": "2025-05-01T00:00:00Z", "summary": SUMMARY},
        {"cycle": 4, "timestamp": "2025-05-02T00:00:00Z", "summary": SUMMARY.replace("Cycle 3", "Cycle 4")},
    ]

    rewritten = future.rewrite_past_into_future(executions, limit=1)

    assert rewritten["meta"]["cycles_rewritten"] == 1
    assert rewritten["meta"]["averages"]["joy"] == 0.97
    assert len(rewritten["future_memory"]) == 1
    entry = rewritten["future_memory"][0]
    assert entry["cycle"] == 4
    assert "Eden88" in entry["future_projection"]
