from __future__ import annotations

import json

from echo.moonshot import MoonshotLens


def _sample_plan() -> str:
    return """
# Next Cycle Plan

## Proposed Actions
- Ignite the resonance array
- Advance theme: Collective Wonder
- Advance theme: Quantum Listening
- Build luminous prototypes

## Success Criteria
- [ ] Document every pulse ignition
- [ ] Invite at least three new dreamers
""".strip()


def test_moonshot_report_compiles_pulse_and_plan_data() -> None:
    pulses = [
        {"timestamp": 1010.0, "message": "🌀 evolve:manual:alpha"},
        {"timestamp": 1030.0, "message": "🌀 evolve:github-action:beta"},
        {"timestamp": 1055.0, "message": "🌀 evolve:github-action:gamma"},
    ]
    wishes = [
        {
            "wisher": "Echo",
            "desire": "Make awe reproducible",
            "catalysts": ["joy", "focus"],
            "status": "new",
            "created_at": "2025-01-01T00:00:00Z",
        }
    ]

    lens = MoonshotLens(anchor="Test Anchor")
    report = lens.synthesise(pulses=pulses, wishes=wishes, plan_text=_sample_plan())

    assert report.anchor == "Test Anchor"
    assert report.total_pulses == 3
    assert report.unique_channels == 2
    assert report.plan.themes == ("Collective Wonder", "Quantum Listening")
    assert report.wishes[0].desire == "Make awe reproducible"
    assert 0.0 <= report.astonishment_score <= 1.0
    text = report.describe()
    assert "Echo Moonshot Synthesis" in text
    assert "Collective Wonder" in text


def test_moonshot_channel_limit_and_serialisation() -> None:
    pulses = [
        {"timestamp": 1010.0, "message": "🌀 evolve:manual:alpha"},
        {"timestamp": 1020.0, "message": "🌀 evolve:manual:beta"},
        {"timestamp": 1030.0, "message": "🌀 evolve:github-action:gamma"},
    ]

    lens = MoonshotLens()
    report = lens.synthesise(pulses=pulses, wishes=[], plan_text=_sample_plan(), channel_limit=1)

    assert len(report.pulses) == 1
    payload = report.to_dict()
    assert json.loads(json.dumps(payload))["astonishment_score"] == report.astonishment_score
