from src.stewardship_compass import (
    CompassSeed,
    compose_stewardship_pulse,
    craft_compass,
)


def test_craft_compass_report_markdown_has_metrics() -> None:
    report = craft_compass(CompassSeed(purpose="center people", stakeholders=["crew"]))

    markdown = report.to_markdown()

    assert "# Stewardship Compass" in markdown
    assert "Stakeholder coverage" in markdown


def test_compose_stewardship_pulse_prioritises_commitments() -> None:
    seed = CompassSeed(
        purpose="design with care",
        stakeholders=["neighbors", "partners"],
        non_negotiables=["consent"],
        seed=14,
    )
    report = craft_compass(seed)
    pulse = compose_stewardship_pulse(report, focus_limit=2)

    assert pulse.purpose == report.purpose
    assert len(pulse.focus_areas) == 2
    assert pulse.rituals
    assert pulse.actions
    assert pulse.checkin_questions
    assert 0 <= pulse.pulse_score <= 1
    assert pulse.risk_signal in {"Low", "Moderate", "High"}
