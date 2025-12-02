import dataclasses
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
    assert result.weakest_year >= 1
    assert 0.0 <= result.volatility <= 1.0
    assert result.pulse_events == config.timelines


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
    assert payload["chaos_distribution"] == "gaussian"
    assert "volatility" in payload
    assert "weakest_year" in payload
    assert len(payload["per_year_strength"]) == 8
    assert len(payload["collapse_histogram"]) == 8
    assert payload["median_failure_year"] is None or payload["median_failure_year"] >= 1
    assert payload["early_warning_year"] is None or payload["early_warning_year"] >= 1
    assert 0.0 <= payload["probability"] <= 1.0
    assert payload["black_swan_events"] >= 0
    assert payload["adaptive_interventions"] >= 0
    assert payload["pulse_events"] >= 0
    assert payload["resilience_dividend"] > 0


def test_uniform_distribution_entropy():
    config = HorizonConfig(
        anchor="Uniform",
        timelines=60,
        years_per_line=10,
        base_resilience=0.9,
        chaos_factor=0.08,
        chaos_distribution="uniform",
        recovery_rate=0.01,
        seed=99,
    )
    engine = HorizonEngine(config=config)
    result = engine.run()

    assert result.failed < config.timelines
    assert 0.0 <= result.volatility <= 1.0
    assert 1 <= result.weakest_year <= config.years_per_line


def test_early_warning_beacon_triggers():
    config = HorizonConfig(
        anchor="Fragile",
        timelines=40,
        years_per_line=6,
        base_resilience=0.5,
        chaos_factor=0.6,
        recovery_rate=0.0,
        seed=21,
        early_warning_threshold=0.2,
    )
    engine = HorizonEngine(config=config)
    result = engine.run()

    assert result.failed > 0
    assert sum(result.collapse_histogram) == result.failed
    assert result.early_warning_year is not None
    assert 1 <= result.early_warning_year <= config.years_per_line


def test_black_swan_shocks_reduce_survival_probability():
    baseline_config = HorizonConfig(
        anchor="Baseline",
        timelines=50,
        years_per_line=6,
        base_resilience=0.9,
        chaos_factor=0.0,
        recovery_rate=0.05,
        seed=123,
        black_swan_chance=0.0,
        black_swan_impact=0.0,
    )
    swan_config = dataclasses.replace(
        baseline_config,
        black_swan_chance=1.0,
        black_swan_impact=0.8,
    )

    baseline_result = HorizonEngine(config=baseline_config).run()
    swan_result = HorizonEngine(config=swan_config).run()

    assert swan_result.failed >= baseline_result.failed
    assert swan_result.black_swan_events > 0


def test_adaptive_recovery_tracks_interventions():
    config = HorizonConfig(
        anchor="Adaptive",
        timelines=10,
        years_per_line=5,
        base_resilience=0.4,
        chaos_factor=0.0,
        recovery_rate=0.1,
        adaptive_recovery=True,
        adaptive_trigger_strength=0.8,
        adaptive_multiplier=3.0,
        black_swan_chance=0.0,
    )
    result = HorizonEngine(config=config).run()

    assert result.survived == config.timelines
    assert result.adaptive_interventions == config.timelines * 2


def test_resonance_pulses_support_fragile_timelines():
    fragile_config = HorizonConfig(
        anchor="Fragile Without Pulses",
        timelines=30,
        years_per_line=8,
        base_resilience=0.45,
        chaos_factor=0.12,
        recovery_rate=0.0,
        seed=2024,
        pulse_interval=0,
    )
    pulsed_config = dataclasses.replace(
        fragile_config,
        anchor="Fragile With Pulses",
        pulse_interval=2,
        pulse_boost=0.1,
    )

    no_pulse_result = HorizonEngine(config=fragile_config).run()
    pulsed_result = HorizonEngine(config=pulsed_config).run()

    assert pulsed_result.pulse_events > 0
    assert pulsed_result.survived >= no_pulse_result.survived
    assert pulsed_result.resilience_dividend >= no_pulse_result.resilience_dividend


def test_fragility_window_detection_flags_low_average():
    config = HorizonConfig(
        anchor="Low Window",
        timelines=20,
        years_per_line=6,
        base_resilience=0.6,
        chaos_factor=0.0,
        recovery_rate=0.0,
        fragility_window=3,
        fragility_threshold=0.7,
        pulse_interval=0,
    )

    result = HorizonEngine(config=config).run()

    assert result.survived == config.timelines
    assert result.fragility_window_start == 1
    assert result.fragility_window_score is not None
