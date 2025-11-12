"""Tests covering the momentum history helpers exposed by :mod:`echo.evolver`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from echo.evolver import EchoEvolver, _MOMENTUM_SENSITIVITY


def test_momentum_history_defaults_to_empty_snapshot() -> None:
    evolver = EchoEvolver()

    snapshot = evolver.advance_system_momentum_history()

    assert snapshot["cycle"] == evolver.state.cycle
    assert snapshot["values"] == []
    assert snapshot["percent_values"] == []
    assert snapshot["sample_count"] == 0
    assert snapshot["window"] is None
    assert snapshot["limit"] is None
    assert snapshot["threshold"] == pytest.approx(_MOMENTUM_SENSITIVITY)


def test_momentum_history_respects_limit_and_preserves_metadata() -> None:
    evolver = EchoEvolver()
    evolver.state.network_cache["advance_system_momentum_history"] = {
        "cycle": 7,
        "values": [0.12, -0.03, 0.05],
        "window": 9,
        "threshold": 0.02,
    }

    snapshot = evolver.advance_system_momentum_history(limit=2)

    assert snapshot["cycle"] == 7
    assert snapshot["values"] == [-0.03, 0.05]
    assert snapshot["percent_values"] == pytest.approx([-3.0, 5.0])
    assert snapshot["sample_count"] == 2
    assert snapshot["window"] == 9
    assert snapshot["limit"] == 2
    assert snapshot["threshold"] == pytest.approx(0.02)


def test_momentum_history_limit_validation() -> None:
    evolver = EchoEvolver()

    with pytest.raises(ValueError):
        evolver.advance_system_momentum_history(limit=0)


def test_advance_system_embeds_momentum_history_when_requested() -> None:
    evolver = EchoEvolver()
    digest = {
        "cycle": 1,
        "progress": 0.5,
        "completed_steps": ["advance_cycle"],
        "remaining_steps": ["mutate_code"],
        "next_step": "Next step: mutate_code() to seed the resonance mutation",
        "steps": [
            {
                "step": "advance_cycle",
                "description": "ignite advance_cycle() to begin the orbital loop",
                "completed": True,
            },
            {
                "step": "mutate_code",
                "description": "seed mutate_code() to stage the resonance mutation",
                "completed": False,
            },
        ],
        "timestamp_ns": 123456789,
    }

    with (
        patch.object(evolver, "run"),
        patch.object(evolver, "cycle_digest", return_value=digest),
        patch.object(evolver, "cycle_digest_report", return_value="report"),
        patch.object(
            evolver,
            "advance_system_momentum_history",
            return_value={"values": [0.25]},
        ) as momentum_history,
    ):
        payload = evolver.advance_system(
            include_status=False,
            include_manifest=False,
            include_reflection=False,
            include_matrix=False,
            include_event_summary=False,
            include_propagation=False,
            include_system_report=False,
            include_diagnostics=False,
            include_momentum_resonance=False,
            include_expansion_history=False,
            include_momentum_history=True,
            momentum_window=3,
            persist_artifact=False,
        )

    momentum_history.assert_called_once_with(limit=3)
    assert payload["momentum_history"] == {"values": [0.25]}
