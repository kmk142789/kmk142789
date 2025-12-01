import json

import pytest

from horizon_engine import HorizonConfig, HorizonEngine, main


def test_engine_run_is_deterministic_with_seed():
    config = HorizonConfig(
        anchor="Test Anchor",
        timelines=200,
        years_per_line=12,
        base_resilience=0.92,
        chaos_factor=0.04,
        recovery_rate=0.02,
        seed=1234,
    )
    engine = HorizonEngine(config=config)
    result = engine.run()

    assert result.survived + result.failed == 200
    assert len(result.per_year_strength) == 12
    assert 0.0 <= result.probability <= 1.0
    assert pytest.approx(1.0) == result.probability


def test_json_output_format(capsys):
    exit_code = main([
        "--timelines",
        "50",
        "--years",
        "8",
        "--seed",
        "7",
        "--format",
        "json",
    ])

    assert exit_code == 0
    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert payload["timelines"] == 50
    assert payload["years_per_line"] == 8
    assert payload["seed"] == 7
    assert len(payload["per_year_strength"]) == 8
    assert 0.0 <= payload["probability"] <= 1.0
