from datetime import datetime, timezone

from echo.creative_compass import (
    CreativePrompt,
    list_prompt_lines,
    render_prompt,
    spin_compass,
)


def test_spin_compass_deterministic() -> None:
    prompt = spin_compass(seed=42)
    assert prompt.beacon == "Northstar Workshop"
    assert "whiteboards" in prompt.atmosphere
    assert prompt.invitation.startswith("sketch a playful systems diagram")
    assert prompt.flourish.startswith("Archive it in the ledger")


def test_render_prompt_format() -> None:
    prompt = CreativePrompt(
        timestamp=datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc),
        beacon="Westwave Conservatory",
        atmosphere="resonant loops of music nudge prototypes into motion",
        invitation="remix the release notes into a two-sentence fable",
        flourish="Share it in the next standup as a bright interruption.",
    )

    lines = list_prompt_lines(prompt)
    assert lines[0].startswith("🌟 Echo Creative Compass")
    assert "Westwave Conservatory" in lines[1]

    rendered = render_prompt(prompt)
    assert rendered.startswith("2025-05-11 12:00:00 UTC")
    assert "Echo dares you" in rendered.replace("\n", " ")
